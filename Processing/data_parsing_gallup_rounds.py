import json
import csv
import os

ACTION_COLUMN = 0  # column containing the actions
ITEM_COLUMN =  3 # column where used mining item is specified
LEADER_SELECTION_ITEM_COLUMN = 2 # column containing the item selected by the leader
PLAYER_ID_COLUMN = 2   # column containing the user id
FOUND_GOLD_COLUMN = 4  # column containing the amount of gold found by the player
TOTAL_GOLD_COLUMN = 2  # column containing the total amount of gold collected by the team
ROUND_SEPARATOR = "GoldSetup"  # when a new round starts
DIVISOR = 50  # when a new state based on the amount of TotalGold has to be created

# players for testing purposes, to be used with the right dataset:  ["af1585u7p7", "Elrric", "sexog53oz3"]
PLAYERS = [
    # "Elrric",
    # "vki5dd5plz",
    # "8grfxa3g9n",
    # "tu1tarrriy",
    # "brjhzjrinm",
    # "z58lm8leyw",
    # "zvq9c5v9gd"
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
        id = str(trajectory[item]) + "_" + str(trajectory[item + 1])  # id: previous node -> current node
        if id not in LINKS:
            LINKS[id] = {'id': id,
                         'source': trajectory[item],
                         'target': trajectory[item + 1],
                         'user_ids': [user_id]}
        else:
            users = LINKS[id]['user_ids']
            users.append(user_id)
            unique_user_set = list(set(users))
            LINKS[id]['user_ids'] = unique_user_set


def parse_data_to_json_format(csv_reader, data_file):
    """
    parse csv data to create node, link and trajectory
    :param csv_reader: raw csv data
    :return:
    """

    #reset dictionaries
    TRAJECTORIES.clear()
    STATES.clear()
    LINKS.clear()

    create_initial_and_final_states()

    # initialize the count the rounds
    round_counter = 0

    user_count = 0

    # loop over each player
    for player in PLAYERS:

        gold_counter = 0
        round_counter = 0
        items_selected = set()
        items_used = set()
        trajectory = [0]  # initialize with start state
        action_meaning = ["start_game"] # used to document the action sequence contained in each trajectory
        key = ""
        update_state(0, player)  # update START state with new user id

        # initialize a state counter (starting from 2 because 0 and 1 are for the initial and final states respectively)
        i = 2

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
                action_meaning.append(action) # append the action here (NOT when gold is found, otherwise only FoundGold is appended)

                if action == "UseItem":
                    items_used.add(row[ITEM_COLUMN])

                if action == "FoundGold":
                    gold_counter = gold_counter + int(row[FOUND_GOLD_COLUMN])

                    # create a new state every time the total gold amount has increased by GOLD_INCREASE
                    if (gold_counter % DIVISOR) == 0:
                        create_or_update_state(i,
                                               "mid",
                                               "",
                                               {'event_type': "gold: "
                                                              + str(gold_counter)
                                                              #+ " - items: " + ', '.join(
                                                             #str(e) for e in items_used)
                                                },
                                               "",
                                               player)
                        # print ("i: " + str(i))
                        # print(STATES[i])

                        # print(', '.join(str(e) for e in items_used))

                        trajectory.append(i)  # append state to the trajectory

                        i = i + 1

            # create a new state every time the voting has finished and a new round has started
            if action == ROUND_SEPARATOR:
                if round_counter > 0:
                    create_or_update_state(i,
                                           "round",
                                           "",
                                           {'event_type': "round "
                                                          + str(round_counter)
                                                          + " - items: "
                                                          + ', '.join(str(e) for e in items_selected)
                                            },
                                           "",
                                           player)

                    print(', '.join(str(e) for e in items_selected))

                    trajectory.append(i)  # append state to the trajectory

                    i = i + 1
                round_counter = round_counter + 1
                items_selected.clear()

            # temporary halt for more than n states
            # if i >= MAX_VISIBLE_STATES:
            #     break

        # print(key)
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
    :param filename: input csv file
    :param action_from_file: if True then finds the actions names from the file; if False then the actions should be
    manually set in the game_actions variable in main
    :return:
    """

    for subdir, dirs, files in os.walk(raw_data_folder):
        ind = 1
        for filename in files:
            # print (os.path.join(rootdir, file))

            file_base = os.path.basename(filename).split('.')[0]
            ext = os.path.basename(filename).split('.')[1]

            if ext == 'csv':
                print(ind, ":", file_base)
                file_names_list.append(file_base)

                with open(raw_data_folder+filename, 'rU') as data_file:
                    csv_reader = csv.reader(data_file)
                    find_players(csv_reader)
                    viz_data = parse_data_to_json_format(csv_reader, data_file)
                    with open(output_folder + file_base + '.json', 'w') as outfile:
                        json.dump(viz_data, outfile)
                        outfile.close()

                    print('\tDone writing to : ' + file_base + '.json')

            ind += 1


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

    create_game_action_dict(GAME_ACTIONS)
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
