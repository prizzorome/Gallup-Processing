import json
import csv
import os

EVENT_COLUMN = 0  # column containing the events (including player actions)
ROUND_SEPARATOR = "GoldSetup"  # when a new round starts

if __name__ == "__main__":
    input_folder = "../data/files_to_check/"
    output_file = "../data/rounds/rounds.csv"

    with open(output_file, 'wb') as csv_output_file:
        writer = csv.writer(csv_output_file)
        writer.writerow(["filename", "round"])

        for subdir, dirs, files in os.walk(input_folder):
            for filename in files:
                print("searching rounds in file: " + filename)
                with open(input_folder + filename, 'rU') as data_file:
                    csv_reader = csv.reader(data_file)
                    round_counter = 0
                    for row in csv_reader:
                        if row[EVENT_COLUMN] == ROUND_SEPARATOR:
                            round_counter = round_counter + 1

                    output_row = [filename, round_counter]

                    writer.writerow(output_row)

        csv_output_file.close()
