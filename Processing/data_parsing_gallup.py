import json
import csv
import os

FOCUS = "teams"  # can be "single_players" or "teams"
FILE_SEPARATOR = ".csv"  # input files must have the .csv extension, otherwise the csv reader does not work
EVENTS_TO_PROCESS = {"round","risk_aversion"}  # events that can be processed: "gold", "round", "distance", "risk_aversion"
CHOSEN_FILENAME = ""  # write a string to override the output file name equal to the source file name
EVENT_COLUMN = 0  # column containing the events (including player actions)
ITEM_NAME_COLUMN = 2  # column where items' names are written during setup
ITEM_PROBABILITY_COLUMN = 4  # column where items' probability of success are written during setup
ITEM_COLUMN = 2  # column where used mining item is specified
START_VOTATION_COLUMN_1 = 2  # column containing 1st mining tool available for voting
START_VOTATION_COLUMN_2 = 3  # column containing 2nd mining tool available for voting
LEADER_SELECTION_ITEM_COLUMN = 2  # column containing the item selected by the leader
PLAYER_ID_COLUMN = 2  # column containing the player id
TEAM_ID_COLUMN = 0  # column containing the filename, used as team ID
FOUND_GOLD_COLUMN = 4  # column containing the amount of gold found by the player
TOTAL_GOLD_COLUMN = 2  # column containing the total amount of gold collected by the team
POSITION_COLUMN = 3  # column containing the start position of "SetDestination" and the "ArrivedTo" position)
ROUND_SEPARATOR = "GoldSetup"  # when a new round starts
GOLD_INCREASE = 100  # when a new state based on the amount of TotalGold has to be created
DISTANCE_INCREASE = 100  # when a new state based on the distance traversed has to be created

MINING_TOOLS = {}  # dictionary of mining tools available to the team, with their probability of success
# manual settings, if needed:
# "Dynamite":         1,
# "RDX":              1,
# "Mine4":            2,
# "SatchelCharge":    2,
# "Mine1":            3,
# "Mine2":            3,
# "Mine3":            3,
# "BlackPowder":      4,
# "TNTbarrel":        4,

PLAYERS = [  # players for testing purposes, to be used with the right dataset:  ["af1585u7p7", "Elrric", "sexog53oz3"]
    # "Elrric",
    # "vki5dd5plz",
    # "8grfxa3g9n",
    # "tu1tarrriy",
    # "brjhzjrinm",
    # "zvq9c5v9gd",
    # "z58lm8leyw"
]

TEAMS = []  # teams (picked from file names)

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

# number of players or teams
TARGET_COUNT = 0

# list of file names
file_names_list = []


def create_initial_and_final_states():
    """
    create all the states/nodes for glyph visualization
    :return:
    """
    state_type = 'start'  # start state
    STATES[0] = {
        'id': 0,  # start node has id 0
        'type': state_type,
        'parent_sequence': [],
        'details': {'event_type': 'start'},
        'stat': {},
        'user_ids': []}

    state_type = 'end'  # end state
    STATES[1] = {
        'id': 1,  # end node has id 1
        'parent_sequence': [],
        'type': state_type,
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


def add_event(event, quantity, target, trajectory, action_sequence, items_selected, success_chance):
    """
    :param event: the event to look up in the states
    :param quantity: the quantity we need to associate with the state
    :param target: the target player or team
    :param trajectory: the trajectory to update
    :param action_sequence: the sequence of actions to update
    :param items_selected: the possible items selected
    :return:
    """
    index = -1
    for key_iterator, value in STATES.items():
        value_list = value['details']['event_type'].split()
        event_name = value_list[0]

        # if an event with a given name and value exists, get its index
        if event_name == event:
            event_number = float(value_list[1])
            if event_number == quantity:
                index = key_iterator
                break

    # if the state already exists update it, otherwise create and append it after the last state
    i = index if index > 0 else STATES.__len__()

    # rounds are a special case
    if event == "round" and items_selected:
        create_or_update_state(i,
                               "round",
                               "",
                               {'event_type': event + " "
                                              + str(quantity)
                                              # + " | avg. quotient: "
                                              # + str(success_chance)
                                              # + " | items: "
                                              # + ', '.join(str(e) for e in items_selected)
                                },
                               "",
                               target)
    # all other cases are default
    else:
        create_or_update_state(i,
                               "mid",
                               "",
                               {'event_type': event + " " + str(quantity)},
                               "",
                               target)

    trajectory.append(i)
    if action_sequence:
        action_sequence.append(i)


def close_graph(trajectory, target, action_sequence, key):
    trajectory.append(1)  # end state
    update_state(1, target)  # update end state with the new user id
    action_sequence.append("end_game")

    add_links(trajectory, target)

    user_ids = [target]

    if key in TRAJECTORIES:
        TRAJECTORIES[key]['user_ids'].append(target)
    else:
        TRAJECTORIES[key] = {'trajectory': trajectory,
                             'action_meaning': action_sequence,
                             'user_ids': user_ids,
                             'id': key,
                             'completed': True}


def process_gold(row, column, gold_counter, accumulation, target, trajectory,action_meaning):
    gold_found = int(row[column])
    if accumulation:
        gold_counter = gold_counter + gold_found
    else: gold_counter = gold_found

    # create a new state every time the total gold amount has increased by DIVISOR (approximate)
    rest_of_division = (float(gold_counter) / GOLD_INCREASE) % 1.0
    remainder = 1.0 - rest_of_division
    if remainder == 1.0 or remainder <= 0.05:
        rounded_gold_counter = roundup(gold_counter)
        add_event("gold:", rounded_gold_counter, target, trajectory, action_meaning, None, None)
        # print("updated gold for target: " + target + " - " + str(rounded_gold_counter))
    return gold_counter


def clear_graph():
    TRAJECTORIES.clear()
    STATES.clear()
    LINKS.clear()


def process_single_players(input_file, file_reader):
    for player in PLAYERS:

        # uncomment next line to experiment only with specific players
        # if player == "z58lm8leyw" or player == "zvq9c5v9gd":

        gold_counter = 0
        round_counter = 0
        items_selected = set()
        items_used = set()
        trajectory = [0]  # initialize trajectory with start state
        action_sequence = ["start_game"]  # used to document the action sequence contained in each trajectory
        key = ""
        new_round = False  # flag used to get the player position when a new round starts
        initial_x = 0  # initial x position of the player when a new round starts
        initial_y = 0  # initial y position of the player when a new round starts
        distance_covered = 0  # total distance covered by the player while moving

        update_state(0, player)  # update START state with new user id

        # "reset" the CSV iterator by resetting the read position of the file object,
        # otherwise the inner loop processes the csv file only once
        input_file.seek(0)

        # update the player's trajectory by processing each row
        for row in file_reader:

            action = row[EVENT_COLUMN]

            if action == "LeaderSelection":
                items_selected.add(row[LEADER_SELECTION_ITEM_COLUMN])

            if row[PLAYER_ID_COLUMN] == player:
                key += ('_' + action)  # generate the key for the trajectory as a sequence of action strings
                # append the action here (NOT when gold is found, otherwise only FoundGold is appended)
                action_sequence.append(action)

                if action == "UseItem":
                    items_used.add(row[ITEM_COLUMN])

                if "gold" in EVENTS_TO_PROCESS and action == "FoundGold":
                    gold_counter = process_gold(row, FOUND_GOLD_COLUMN, True, gold_counter, player, trajectory, action_sequence)

                # TODO: if covered distance is useful, convert the code for processing it into a function
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
                            rounded_distance_counter = roundup(distance_covered)
                            add_event("distance:", rounded_distance_counter, player, trajectory, action_sequence, None,
                                      None)

            if "round" in EVENTS_TO_PROCESS and action == ROUND_SEPARATOR:
                # start creating new states based on rounds after the first gold_setup (because
                # the very first one occurs at the beginning of the game) and avoid
                # updating the action sequence because rounds are not player's actions
                if round_counter > 0:
                    add_event("round", round_counter, player, trajectory, None, items_selected, None)
                    print("added round event num: " + str(round_counter))

                round_counter = round_counter + 1
                items_selected.clear()

        # ------ close states, trajectories and links, update target count, clear mining tools
        close_graph(trajectory, player, action_sequence, key)

        # increase the count of targets
        global TARGET_COUNT
        TARGET_COUNT = TARGET_COUNT + 1

        # clear the mining tools
        MINING_TOOLS.clear()


def parse_data_to_json_format(csv_reader, data_file):
    """
    parse csv data to create node, link and trajectory
    :param csv_reader: raw csv data
    :param data_file: input file
    :return:
    """

    # reset graph and initialize states
    clear_graph()
    create_initial_and_final_states()

    if FOCUS == "single_players":
        process_single_players(data_file, csv_reader)
    elif FOCUS == "teams":
        # "reset" the CSV iterator by resetting the read position of the file object,
        # otherwise the inner loop processes the csv file only once
        data_file.seek(0)

        initial_team = ""

        for row in csv_reader:

            first_cell = row[TEAM_ID_COLUMN]

            if first_cell in TEAMS:
                team = first_cell

                if team != initial_team:

                    print("---starting to process new team: " + team)

                    # ------ close previous team's states, trajectories and links
                    if initial_team != "":
                        close_graph(trajectory, initial_team, event_sequence, key)
                        # increase the count of targets
                        global TARGET_COUNT
                        TARGET_COUNT = TARGET_COUNT + 1
                        # clear the mining tools
                        MINING_TOOLS.clear()

                    # initialize variables
                    gold_counter = 0
                    round_counter = 0
                    items_selected = []
                    selection_counter = 0
                    selected_items_quotient_sum = 0
                    num_of_items = 0

                    # initialize trajectory, action sequence and key
                    trajectory = [0]  # initialize with start state
                    event_sequence = ["start_game"]
                    key = ""

                    # update START state with new target id
                    update_state(0, team)

                    # update initial team
                    initial_team = team

            event = row[EVENT_COLUMN]

            if event == "ItemSetup":
                MINING_TOOLS[row[ITEM_COLUMN]] = row[ITEM_PROBABILITY_COLUMN]
                # print ("MINING_TOOLS: " + str(MINING_TOOLS))
            elif event == "MineSetup":
                prob_string = row[ITEM_PROBABILITY_COLUMN]
                # mines have a min and max probability of success: we store their mean in MINING_TOOLS
                prob_list = prob_string.translate(None, '()').split()
                floor = float(prob_list[0])
                ceiling = float(prob_list[1])
                MINING_TOOLS[row[ITEM_COLUMN]] = (floor + ceiling)/2
                # print ("MINING_TOOLS: " + str(MINING_TOOLS))

            # if the event is different from the team name,
            # append it to the key that distinguishes sequence graph nodes (i.e. players or teams)
            # and to the sequence of actions, and pick the mining tool if it's in the event
            if event != team:
                key += ('_' + event)
                # append the event here (NOT when specific events happen, otherwise only those events are appended)
                event_sequence.append(event)

            if event == "StartVotation":
                item1_prob = float(MINING_TOOLS[row[START_VOTATION_COLUMN_1]])
                item2_prob = float(MINING_TOOLS[row[START_VOTATION_COLUMN_2]])
                mining_tools_prob_sum = item1_prob + item2_prob  # sum of success probs. of mining tools to choose from
                print("--- items to choose from: " +
                      row[2] + "(" + str(item1_prob) + ")" + ", " +
                      row[3] + "(" + str(item2_prob) + ")" +
                      " - sum of probabilities: " + str(mining_tools_prob_sum))

            if round_counter > 0 and event == "LeaderSelection":
                item = row[LEADER_SELECTION_ITEM_COLUMN]
                items_selected.append(item)
                print("item selected: " + item)
                if item in MINING_TOOLS:
                    num_of_items = num_of_items + 1
                    probability_quotient = float(MINING_TOOLS[item]) / mining_tools_prob_sum
                    selected_items_quotient_sum = selected_items_quotient_sum + probability_quotient
                    selection_counter = selection_counter + 1
                    print ("... MINING_TOOLS[" + item + "]: " + str(MINING_TOOLS[item]))
                    print("... probability_quotient: " + str(probability_quotient))
                    print("... sum of probability quotients: " + str( selected_items_quotient_sum))
                    print("... selection counter: " + str(selection_counter))

            if "gold" in EVENTS_TO_PROCESS and event == "TotalGold":
                gold_counter = process_gold(row, TOTAL_GOLD_COLUMN, False, gold_counter, team, trajectory, event_sequence)

            if "round" in EVENTS_TO_PROCESS and event == ROUND_SEPARATOR:

                    # start creating new states based on rounds after first gold_setup (because
                    # the very first gold_setup occurs at the beginning of the game)
                    # and avoid updating the action sequence because rounds are not player's actions
                    if round_counter > 0 and num_of_items > 0:
                        # compute the average quotient and then reset its components
                        avg_selected_item_success_prob = round(float(selected_items_quotient_sum) / selection_counter, 2)
                        num_of_items = 0
                        selected_items_quotient_sum = 0
                        selection_counter = 0

                        if "risk_aversion" in EVENTS_TO_PROCESS:
                            add_event("risk_aversion", str(avg_selected_item_success_prob), team, trajectory, None, items_selected,
                                      str(avg_selected_item_success_prob))

                        # add the round event
                        add_event("round", round_counter, team, trajectory, None, items_selected, avg_selected_item_success_prob)
                        print("added round event num: " + str(round_counter))
                        print(">>>>>>>>>> avg_selected_item_success_prob: " + str(avg_selected_item_success_prob))

                    round_counter = round_counter + 1

                    items_selected = []

            # if it's end of file, close the graph of the current team
            if first_cell == "END" and team != "" and team in TEAMS:
                close_graph(trajectory, team, event_sequence, key)
                # increase the count of targets
                global TARGET_COUNT
                TARGET_COUNT = TARGET_COUNT + 1
                # clear the mining tools
                MINING_TOOLS.clear()

    # ------ RETURN RESULTS
    # generate lists from dictionaries
    state_list = list(STATES.values())
    link_list = list(LINKS.values())
    trajectory_list = list(TRAJECTORIES.values())

    # return the results
    return {'level_info': 'Visualization',
            'num_patterns': TARGET_COUNT,
            'num_users': TARGET_COUNT,
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

    for col in csv_reader:
        actions = col[EVENT_COLUMN:]

        for item in actions:
            if item == "":
                break
            if item not in ACTIONS:
                ACTIONS[item] = count_action
                count_action += 1


def find_players(csv_reader):
    """
    finds the player names in the csv file
    :param csv_reader: input file
    :return:
    """
    for row in csv_reader:
        if row[EVENT_COLUMN] == "PlayerConnection":
            PLAYERS.append(row[PLAYER_ID_COLUMN])


def find_teams(csv_reader):
    """
    finds the teams in the csv file
    :param csv_reader: input file
    :return:
    """
    for row in csv_reader:
        team = row[TEAM_ID_COLUMN]
        if team.find(FILE_SEPARATOR) > -1:
            TEAMS.append(team)


def process_data(input_folder, out_folder, action_from_file=True):
    """
    process each csv file to create the json file for glyph
    :param input_folder: folder containing raw data files
    :param out_folder: output folder
    :param action_from_file: if True then finds the actions names from the file; if False then the actions should be
    manually set in the game_actions variable in main
    :return:
    """

    create_initial_and_final_states()

    for subdir, dirs, files in os.walk(input_folder):
        ind = 0
        for filename in files:
            # print (os.path.join(rootdir, file))

            if CHOSEN_FILENAME == "":
                output_file = os.path.basename(filename).split('.')[0]
            else: output_file = CHOSEN_FILENAME

            ext = os.path.basename(filename).split('.')[1]

            if ext == 'csv':
                print(ind, ":", output_file)
                file_names_list.append(output_file)

                with open(input_folder + filename, 'rU') as data_file:
                    csv_reader = csv.reader(data_file)

                    if FOCUS == "single_players":
                        find_players(csv_reader)
                    elif FOCUS == "teams":
                        find_teams(csv_reader)

                    viz_data = parse_data_to_json_format(csv_reader, data_file)

                    print('\tDone writing to : ' + output_file + '.json')
                    ind += 1

            with open(out_folder + output_file + '.json', 'w') as outfile:
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
