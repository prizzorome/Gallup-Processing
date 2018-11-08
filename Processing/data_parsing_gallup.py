import json
import csv
import os

FOCUS = "teams"  # can be "single_players" or "teams"
EVENTS_TO_PROCESS = {"gold", "round"}  # events to process  , "distance"
CHOSEN_FILENAME = "0814_noncompetitive_TEAM_gold+rounds+chances"  # use this to override the output file name equal to the source file name
ACTION_COLUMN = 0  # column containing the actions
ITEM_COLUMN = 3  # column where used mining item is specified
LEADER_SELECTION_ITEM_COLUMN = 2  # column containing the item selected by the leader
PLAYER_ID_COLUMN = 2  # column containing the user id
FOUND_GOLD_COLUMN = 4  # column containing the amount of gold found by the player
TOTAL_GOLD_COLUMN = 2  # column containing the total amount of gold collected by the team
POSITION_COLUMN = 3  # column containing the start position of "SetDestination" and the "ArrivedTo" position)
ROUND_SEPARATOR = "GoldSetup"  # when a new round starts
GOLD_INCREASE = 100  # when a new state based on the amount of TotalGold has to be created
DISTANCE_INCREASE = 100 # when a new state based on the distance traversed has to be created
GRID_START = 0  # first x or y position of the grid
GRID_HALF = 29  # x or y position of the first half of the grid
GRID_END = 59  # last x or y position of the grid
SW = NW = range(GRID_START, GRID_HALF + 1)  # second number in range() is exclusive, so we need to increment it by 1
SE = NE = range(GRID_HALF + 1, GRID_END + 1)  # second number in range() is exclusive, so we need to increment it by 1
MINING_TOOLS_PROB_SUCCESS = {
    "Dynamite":         1,
    "RDX":              1,
    "Mine4":            2,
    "SatchelCharge":    2,
    "Mine1":            3,
    "Mine2":            3,
    "Mine3":            3,
    "BlackPowder":      4,
    "TNTbarrel":        4,
}
# players for testing purposes, to be used with the right dataset:  ["af1585u7p7", "Elrric", "sexog53oz3"]
PLAYERS = [
    # "Elrric",
    # "vki5dd5plz",
    # "8grfxa3g9n",
    # "tu1tarrriy",
    # "brjhzjrinm",
    # "zvq9c5v9gd",
    # "z58lm8leyw"
]

GAME_ACTIONS = [
    "ArrivedTo",
    "CensoredMessage",
    "ChatMessage",
    "DestroyRock",
    "FoundGold",
    "MiningPickaxe",
    "NewLeader",
    "PlayerConnection",
    "SelectItem",
    "SetDestination",
    "UseItem",
    "Vote"
]

# dictionaries
ACTIONS = {}
STATES = {}
TRAJECTORIES = {}
LINKS = {}

file_names_list = []


def create_initial_and_final_states():
    """
    create all the states/nodes for glyph visualization
    :return:
    """
    stateType = 'start'  # start state
    STATES[0] = {
        'id': 0,  # start node has id 0
        'type': stateType,
        'parent_sequence': [],
        'details': {'event_type': 'start'},
        'stat': {},
        'user_ids': []}

    stateType = 'end'  # end state
    STATES[1] = {
        'id': 1,  # end node has id 1
        'parent_sequence': [],
        'type': stateType,
        'details': {'event_type': 'end'},
        'stat': {},
        'user_ids': []}


def update_state(state_id, user_id):
    STATES[state_id]['user_ids'].append(user_id)


def create_or_update_state(state_id, state_type, parent_sequence, details, stat, user_id):
    # print ("state_type :" + str(state_type))
    # print ("details: " + str(details))
    if state_id in STATES:
            STATES[state_id]['type'] = state_type
            STATES[state_id]['parent_sequence'] = parent_sequence
            STATES[state_id]['details'] = details
            STATES[state_id]['stat'] = stat

            if user_id not in STATES[state_id]['user_ids']:
                STATES[state_id]['user_ids'].append(user_id)
    else:
        STATES[state_id] = {
            'id': state_id,
            'type': state_type,
            'parent_sequence': parent_sequence,
            'details': details,
            'stat': stat,
            'user_ids': [user_id]}


def add_links(trajectory, user_id):
    """
    adds link between the consecutive nodes of the trajectory
    :param trajectory:
    :param user_id:
    :return:
    """
    for item in range(0, len(trajectory) - 1):
        uid = str(trajectory[item]) + "_" + str(trajectory[item + 1])  # id: previous node -> current node
        if uid not in LINKS:
            LINKS[uid] = {'id': uid,
                         'source': trajectory[item],
                         'target': trajectory[item + 1],
                         'user_ids': [user_id]}
        else:
            users = LINKS[uid]['user_ids']
            users.append(user_id)
            unique_user_set = list(set(users))
            LINKS[uid]['user_ids'] = unique_user_set



def roundup(x):
    return x if x % GOLD_INCREASE == 0 else x + GOLD_INCREASE - x % 100


def add_event(target_event, counter, player, trajectory, action_meaning, items_selected, success_chance):
    """
    :param target_event: the event to look up in the states
    :param counter: the counter we need to associate with the state
    :param player: the target player
    :param trajectory: the trajectory to update
    :param action_meaning: the sequence of actions to update
    :param items_selected: the possible items selected
    :return:
    """
    index = -1
    for key_iterator, value in STATES.items():
        value_list = value['details']['event_type'].split()
        event_name = value_list[0]

        # if an event with a given name and value exists, get its index
        if event_name == target_event:
            event_number = int(value_list[1])
            if event_number == counter:
                index = key_iterator
                break

    # if the state already exists update it, otherwise create and append it after the last state
    i = index if index > 0 else STATES.__len__()

    # rounds are a special case
    if target_event == "round" and items_selected:
        create_or_update_state(i,
                               "round",
                               "",
                               {'event_type': target_event + " "
                                              + str(counter)
                                              + " | avg. chance: "
                                              + str(success_chance)
                                              + " | items: "
                                              + ', '.join(str(e) for e in items_selected)
                                },
                               "",
                               player)
    # all other cases are default
    else:
        create_or_update_state(i,
                               "mid",
                               "",
                               {'event_type': target_event + " " + str(counter)},
                               "",
                               player)

    trajectory.append(i)
    if action_meaning:
        action_meaning.append(i)


def parse_data_to_json_format(csv_reader, data_file, team):
    """
    parse csv data to create node, link and trajectory
    :param csv_reader: raw csv data
    :return:
    """

    # reset dictionaries
    TRAJECTORIES.clear()
    STATES.clear()
    LINKS.clear()

    create_initial_and_final_states()

    user_count = 0

    if FOCUS == "single_players":
        # loop over each player
        for player in PLAYERS:

            # if player == "z58lm8leyw" or player == "zvq9c5v9gd":

                gold_counter = 0
                rounded_gold_counter = 0
                round_counter = 0
                items_selected = set()
                items_used = set()
                trajectory = [0]  # initialize with start state
                action_meaning = ["start_game"]  # used to document the action sequence contained in each trajectory
                key = ""
                new_round = False # flag used to get the player position when a new round starts
                initial_x = 0 # initial x position of the player when a new round starts
                initial_y = 0  # initial y position of the player when a new round starts
                distance_covered = 0 # total distance covered by the player while moving
                rounded_distance_counter = 0 #

                update_state(0, player)  # update START state with new user id

                # initial_position_counter = 0
                # initial_quadrant = ""
                # new_quadrant = ""

                # initialize a state counter (starting from 2 because 0 and 1 are for the initial and final states respectively)
                # i = 2

                # "reset" every time the CSV iterator by resetting the read position of the file object,
                # otherwise the inner loop processes the csv file only once
                data_file.seek(0)

                # update the player's trajectory by processing each row
                for row in csv_reader:

                    action = row[ACTION_COLUMN]

                    if action == "LeaderSelection":
                        items_selected.add(row[LEADER_SELECTION_ITEM_COLUMN])

                    if row[PLAYER_ID_COLUMN] == player:
                        key += ('_' + action)  # generate the key for the trajectory as a sequence of action strings
                        # append the action here (NOT when gold is found, otherwise only FoundGold is appended)
                        action_meaning.append(action)

                        if action == "UseItem":
                            items_used.add(row[ITEM_COLUMN])

                        if "gold" in EVENTS_TO_PROCESS and action == "FoundGold":
                            gold_found = int(row[FOUND_GOLD_COLUMN])
                            gold_counter = gold_counter + gold_found

                            # create a new state every time the total gold amount has increased by DIVISOR (approximate)
                            rest_of_division = (float(gold_counter) / GOLD_INCREASE) % 1.0
                            remainder = 1.0 - rest_of_division
                            if remainder == 1.0 or remainder <= 0.05:
                                rounded_gold_counter = rounded_gold_counter + roundup(gold_counter)
                                add_event("gold:", rounded_gold_counter, player,trajectory, action_meaning, None, None)
                                print("updated gold for player: " + player + " - " + str(rounded_gold_counter))
                                rounded_gold_counter = 0

                        if "distance" in EVENTS_TO_PROCESS and action == "ArrivedTo":
                            if new_round:
                                # get the player's initial position at the start of the new round
                                initial_position = row[POSITION_COLUMN]
                                initial_position = initial_position.translate(None, '()').split()
                                initial_x = int(initial_position[0])
                                initial_y = int(initial_position[1])
                                # reset the flag that triggers the getting of the initial position
                                new_round = False
                            else:
                                position = row[POSITION_COLUMN]
                                position = position.translate(None, '()').split()
                                print("player " + player + " position: " + str(position))
                                x = int(position[0])
                                y = int(position[1])
                                distance_covered = distance_covered + abs(x - initial_x) + abs(y - initial_y)
                                initial_x = x
                                initial_y = y
                                print("distance_covered: " + str(distance_covered))

                                # create a new state every time total distance has increased by DIVISOR (approximate)
                                rest_of_division = (float(distance_covered) / DISTANCE_INCREASE) % 1.0
                                remainder = 1.0 - rest_of_division
                                if remainder == 1.0 or remainder <= 0.02:
                                    rounded_distance_counter = rounded_distance_counter + roundup(distance_covered)
                                    add_event("distance:", rounded_distance_counter, player, trajectory, action_meaning, None, None)
                                    rounded_distance_counter = 0

                    if "round" in EVENTS_TO_PROCESS and action == ROUND_SEPARATOR:
                        # turn on the flag to get the initial player's position
                        new_round = True

                        # start creating new states based on rounds after the first gold_setup (because the very first one
                        # occurs at the beginning of the game)
                        # and avoid updating the action sequence because rounds are not player's actions
                        if round_counter > 0:
                            add_event("round", round_counter, player, trajectory, None, items_selected, None)
                            print("added round event num: " + str(round_counter))

                        round_counter = round_counter + 1
                        items_selected.clear()

                trajectory.append(1)  # end state
                update_state(1, player)  # update end state with the new user id
                action_meaning.append("end_game")

                add_links(trajectory, player)

                user_ids = [player]

                if key in TRAJECTORIES:
                    TRAJECTORIES[key]['user_ids'].append(player)
                else:
                    TRAJECTORIES[key] = {'trajectory': trajectory,
                                         'action_meaning': action_meaning,
                                         'user_ids': user_ids,
                                         'id': key,
                                         'completed': True}

                # NOTE: the user_count is NOT updated in the original code, but I thought it should be
                user_count = user_count + 1

    elif FOCUS == "teams":
        # loop over each team
        # for player in PLAYERS:
        rounded_gold_counter = 0
        round_counter = 0
        items_selected = []
        num_of_items = 0
        sum_of_item_success_chances = 0
        trajectory = [0]  # initialize with start state
        action_meaning = ["start_game"]  # used to document the action sequence contained in each trajectory
        key = ""

        update_state(0, team)  # update START state with new user id

        # "reset" every time the CSV iterator by resetting the read position of the file object,
        # otherwise the inner loop processes the csv file only once
        data_file.seek(0)

        # update the team's trajectory by processing each row
        for row in csv_reader:

            action = row[ACTION_COLUMN]

            if round_counter > 0 and action == "LeaderSelection":
                item = row[LEADER_SELECTION_ITEM_COLUMN]
                items_selected.append(item)
                if item in MINING_TOOLS_PROB_SUCCESS:
                    num_of_items = num_of_items + 1
                    sum_of_item_success_chances = sum_of_item_success_chances + MINING_TOOLS_PROB_SUCCESS[item]

            # TODO: use FoundGold instead of TotalGold
            if "gold" in EVENTS_TO_PROCESS and action == "TotalGold":
                gold_counter = int(row[TOTAL_GOLD_COLUMN])

                if gold_counter >= GOLD_INCREASE:
                    # create a new state every time the total gold amount has increased by DIVISOR (approximate)
                    rest_of_division = (float(gold_counter) / GOLD_INCREASE) % 1.0
                    remainder = 1.0 - rest_of_division
                    if remainder == 1.0 or remainder <= 0.05:
                        rounded_gold_counter = rounded_gold_counter + roundup(gold_counter)
                        add_event("gold:", rounded_gold_counter, team, trajectory, action_meaning, None, None)
                        print("updated gold for team: " + str(team) + " - " + str(rounded_gold_counter))
                        rounded_gold_counter = 0

            if "round" in EVENTS_TO_PROCESS and action == ROUND_SEPARATOR:

                key += ('_' + action)  # generate the key for the trajectory as a sequence of action strings
                # append the action here (NOT when gold is found, otherwise only FoundGold is appended)
                action_meaning.append(action)

                # start creating new states based on rounds after first gold_setup (because
                # the very first gold_setup occurs at the beginning of the game)
                # and avoid updating the action sequence because rounds are not player's actions
                if round_counter > 0:
                    # compute the average chance of success and then reset its components
                    average_item_success_chance = round(float(sum_of_item_success_chances) / float(num_of_items), 1)
                    num_of_items = 0
                    sum_of_item_success_chances = 0
                    # add the event
                    add_event("round", round_counter, team, trajectory, None, items_selected, average_item_success_chance)
                    print("added round event num: " + str(round_counter))

                round_counter = round_counter + 1

                items_selected = []

        trajectory.append(1)  # end state
        update_state(1, team)  # update end state with the new user id
        action_meaning.append("end_game")

        add_links(trajectory, team)

        user_ids = [team]

        if key in TRAJECTORIES:
            TRAJECTORIES[key]['user_ids'].append(team)
        else:
            TRAJECTORIES[key] = {'trajectory': trajectory,
                                 'action_meaning': action_meaning,
                                 'user_ids': user_ids,
                                 'id': key,
                                 'completed': True}

        # NOTE: the user_count is NOT updated in the original code, but I thought it should be
        user_count = user_count + 1

    # generate lists from dictionaries
    state_list = list(STATES.values())
    link_list = list(LINKS.values())
    trajectory_list = list(TRAJECTORIES.values())

    return {'level_info': 'Visualization',
            'num_patterns': user_count,
            'num_users': user_count,
            'nodes': state_list,
            'links': link_list,
            'trajectories': trajectory_list,
            'traj_similarity': [],
            'setting': 'test'}


def find_actions(csv_reader):
    """
    finds the action names in the csv file
    :param csv_reader: input file
    :return:
    """
    global ACTIONS
    ACTIONS = {}
    count_action = 0

    # paola 180911: in next FOR loop used columns instead of rows
    for col in csv_reader:
        actions = col[ACTION_COLUMN:]

        for item in actions:
            if item == "":
                break
            if item not in ACTIONS:
                ACTIONS[item] = count_action
                count_action += 1


def find_players(csv_reader):
    """
    finds the action names in the csv file
    :param csv_reader: input file
    :return:
    """
    # paola 180911: in next FOR loop used columns instead of rows
    for row in csv_reader:
        if (row[ACTION_COLUMN] == "PlayerConnection"):
            PLAYERS.append(row[PLAYER_ID_COLUMN])


def process_data(raw_data_folder, output_folder, action_from_file=True):
    """
    process each csv file to create the json file for glyph
    :param raw_data_folder: folder containing raw data files
    :param output_folder: output folder
    :param action_from_file: if True then finds the actions names from the file; if False then the actions should be
    manually set in the game_actions variable in main
    :return:
    """

    create_initial_and_final_states()


    for subdir, dirs, files in os.walk(raw_data_folder):
        ind = 0
        for filename in files:
            # print (os.path.join(rootdir, file))

            # output_file = os.path.basename(filename).split('.')[0]
            output_file = CHOSEN_FILENAME
            ext = os.path.basename(filename).split('.')[1]

            if ext == 'csv':
                print(ind, ":", output_file)
                file_names_list.append(output_file)

                with open(raw_data_folder + filename, 'rU') as data_file:
                    csv_reader = csv.reader(data_file)

                    if FOCUS == "single_players":
                        find_players(csv_reader)

                    viz_data = parse_data_to_json_format(csv_reader, data_file, ind)

                    print('\tDone writing to : ' + output_file + '.json')
                    ind += 1

    # moved next WITH clause out of the loop
    with open(output_folder + output_file + '.json', 'w') as outfile:
        json.dump(viz_data, outfile)
        outfile.close()




def create_game_action_dict(actions):
    """
    initializes the dictionary ACTION with the actions and assigns a unique number to each action
    :param actions: a list containing the action names
    :return:
    """
    count_action = 0
    for action in actions:
        ACTIONS[action] = count_action
        count_action += 1


if __name__ == "__main__":
    # manually set actions

    # create_game_action_dict(GAME_ACTIONS)
    # print(ACTIONS)

    raw_data_folder = "../data/raw/"
    output_folder = "../data/output/"

    process_data(raw_data_folder, output_folder, action_from_file=True)
    # print(ACTIONS)
    # print(STATES)

    # print("File names of visualization_ids.json")
    # print(json.dumps(file_names_list))

    # generate the visualization_ids.json file
    with open(output_folder + 'visualization_ids.json', 'w') as outfile:
        json.dump(file_names_list, outfile)
        outfile.close()
        print("\nvisualization_ids.json file generated.")
