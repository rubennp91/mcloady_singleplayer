import keyboard
import configparser
import os
from time import sleep
from datetime import timedelta


def send_tp(x, y, z, a, b):
    """
    Send the telepor command using mcr. 'x', 'y' 'z'
    are cartesian coordinates, 'a' and 'b' are angles.
    """
    tp_parameters = [str(i) for i in ["/tp @p", x, y, z, a, b]]
    mc_command = ' '.join(tp_parameters)
    keyboard.press_and_release('t')
    sleep(0.1)
    keyboard.write(mc_command)
    sleep(0.1)
    keyboard.press_and_release('enter')


def generate_node(x, y, z, first_wait, second_wait):
    """
    Generate a node using the coordinates and angles. Take in the
    Minecraft RCON object, the coordinates, the primary and secondary
    wait times.
    """
    send_tp(x, y, z, -90, 20)
    sleep(first_wait)
    send_tp(x, y, z, 0, 20)
    sleep(second_wait)
    send_tp(x, y, z, 90, 20)
    sleep(second_wait)
    send_tp(x, y, z, 180, 20)
    sleep(second_wait)


def read_last_tp(config):
    """
    If program was executed previously, a 'last_tp.txt'
    file will exist. Use the coordinates inside to
    start iterating from there. If it doesnt exist,
    set the initial coordinates using the parameters
    in the configuration file.
    """
    save_file = config['FILE']['last_tp']
    if not os.path.isfile(save_file):
        altitude = config['PARAMETERS']['altitude']
        # X, Z, dX, dZ, start_i
        last_tp = [0, 0, 0, -1, 0]
        with open(save_file, 'w') as f:
            f.write(','.join(str(x) for x in last_tp))
    else:
        with open(save_file, 'r') as f:
            last_tp = f.read()
        last_tp = last_tp.split(',')
    return last_tp, save_file


def calculate_time_remaining(i, normalized_nodes, first_wait, second_wait):
    """
    Function to calculate the time remaining on the script.
    This can be done by checking the iteration number of
    and the total number of nodes to be generated. Subtracting
    the two gives the increments left to be generated. Multiplying by the
    time required for each node to be generated gives the time left.
    """
    total_iterations_left = normalized_nodes - i
    time_per_iteration = first_wait + second_wait*3

    total_time_remaining = total_iterations_left*time_per_iteration

    return str(timedelta(seconds=total_time_remaining))


def main(config):
    """
    The main function reads the parameters from the config file.
    It also calls the tp function using the spiral algorithm
    as well as saves the last tp position.
    """
    last_tp, save_file = read_last_tp(config)

    print("The program will execute now. You will not be able to use your "
          "computer while the program is executing. It is recommended that "
          "you unplug your keyboard and mouse once the program has started. "
          "If you wish to stop the program, return to the terminal and press "
          "'Del'.")

    input("Press enter to start...")
    print("Starting in 5 seconds...")
    sleep(5)

    radius = int(config['PARAMETERS']['radius'])
    increments = int(config['PARAMETERS']['increments'])
    y = int(config['PARAMETERS']['altitude'])
    first_wait = int(config['PARAMETERS']['first_wait'])
    second_wait = int(config['PARAMETERS']['second_wait'])

    # Load last saved tp coordinates, next increment, and current iteration.
    x = int(last_tp[0])
    z = int(last_tp[1])
    dx = int(last_tp[2])
    dz = int(last_tp[3])
    start_i = int(last_tp[4])

    # 2D Spiral Algorithm
    # https://stackoverflow.com/questions/398299/looping-in-a-spiral
    normalized_radius = radius / increments
    normalized_diameter = normalized_radius * 2
    normalized_nodes = round(normalized_diameter ** 2)
    iterator = start_i

    while iterator < normalized_nodes:
        if (-normalized_radius <= x <= normalized_radius) and \
           (-normalized_radius <= z <= normalized_radius):
            actual_x = int(x * increments)
            actual_z = int(z * increments)
            generate_node(actual_x,
                          y,
                          actual_z,
                          first_wait,
                          second_wait,
                          )

            with open(save_file, 'w') as f:
                # Write position and next step to file
                f.write("{0},{1},{2},{3},{4}\n".format(x, z, dx, dz, iterator))

            remaining_time = calculate_time_remaining(iterator,
                                                      normalized_nodes,
                                                      first_wait,
                                                      second_wait)

            print("Player teleported to position:", str(actual_x), str(y), str(actual_z))
            print("Player teleported to normalized position:", x, str(y), z)
            print("{0}/{1} nodes completed. {2} left."
                  .format(iterator, normalized_nodes,
                          (normalized_nodes - iterator)))
            print("Approximate remaining time:", remaining_time)

            if x == z or (x < 0 and x == -z) or (x > 0 and x == 1-z):
                dx, dz = -dz, dx

            x, z = x+dx, z+dz

        iterator += 1

    print("All finished!")


if __name__ == '__main__':
    config = configparser.ConfigParser()
    config.read("config.ini")
    main(config)
