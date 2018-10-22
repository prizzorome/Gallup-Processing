import json
import csv
import os

ACTION_START = 9  # column from where action names start in csv file;
                # change if the format of data is different in different files
PART1_ID = 0  # column used for the user id part 1
PART2_ID = 7  # column used for the user id part 2

ACTIONS = {}
STATES = {}
TRAJECTORIES = {}
LINKS = {}

file_names_list = []


def create_node():
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

    stateType = 'mid'
    for action in ACTIONS:
        # print(ACTIONS[action])
        STATES[ACTIONS[action] + 2] = {
            'id': ACTIONS[action] + 2,  # other state has id ranging from 3
            'parent_sequence': [],
            'type': stateType,
            'details': {'event_type': action},
            'stat': {},
            'user_ids': []}


def update_state(state_id, user_id):
    STATES[state_id]['user_ids'].append(user_id)


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


def create_trajectory(row, user_id):
    """
    creates trajectory for the given actions of the user
    :param row: the actions of the user
    :param user_id:
    :return:
    """
    trajectory = [0]  # initialize with start state
    action_meaning = ["start_game"]
    key = ""

    update_state(0, user_id)  # update start state with new used id

    action_flag = {}  # keep track which state already have the user id
    for action in ACTIONS:
        action_flag[action] = False

    for item in row:
        if item == "":
            break
        key += ('_'+item)  # generate id for the trajectory
        trajectory.append(ACTIONS[item] + 2)  # append state to the trajectory
        action_meaning.append("transition")  # append action meaning. may use different meaning for different types
                                            # of transition
        if not action_flag[item]:  # check if the user already got to that state before, if so then no need to update
            action_flag[item] = True
            update_state(ACTIONS[item] + 2, user_id)

    # print(key)
    trajectory.append(1)  # end state
    update_state(1, user_id)  # update end state with the new used id
    action_meaning.append("end_game")

    add_links(trajectory, user_id)

    user_ids = [user_id]

    if key in TRAJECTORIES:
        TRAJECTORIES[key]['user_ids'].append(user_id)
    else:
        TRAJECTORIES[key] = {'trajectory': trajectory,
                             'action_meaning': action_meaning,
                             'user_ids': user_ids,
                             'id': key,
                             'completed': True}


def parse_data_to_json_format(csv_reader):
    """
    parse csv data to create node, link and trajectory
    :param csv_reader: raw csv data
    :return:
    """
    create_node()  # create all the states for glyph
    user_count = 0

    for row in csv_reader:
        user_id = row[PART1_ID] + '_' + row[PART2_ID]  # generate user id
        create_trajectory(row[ACTION_START:len(row)], user_id)

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
    for row in csv_reader:
        actions = row[ACTION_START:]

        for item in actions:
            if item == "":
                break
            if item not in ACTIONS:
                ACTIONS[item] = count_action
                count_action += 1


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

                if action_from_file:
                    with open(raw_data_folder+filename, 'rU') as data_file:
                        csv_reader = csv.reader(data_file)
                        next(csv_reader, None)
                        find_actions(csv_reader)

                with open(raw_data_folder+filename, 'rU') as data_file:
                    csv_reader = csv.reader(data_file)
                    next(csv_reader, None)
                    viz_data = parse_data_to_json_format(csv_reader)
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
    game_actions = \
        ["briefcase_locked",
            "briefcase_unlocked",
            "open_fax_log",
            "fax_log_delete",
            "shred",
            "call",
            "conjecture",
            "enter_room",
            "fax",
            "notebook_page",
            "pickup",
            "put_down"]

    create_game_action_dict(game_actions)
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
