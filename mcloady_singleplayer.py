import keyboard
import configparser
import os
from time import sleep
from datetime import timedelta


def str2bool(v):
  return v.lower() in ("yes", "true", "t", "1")


def send_cmd(cmd):
    for i in cmd:
        keyboard.press_and_release('t')
        sleep(0.1)
        keyboard.write(i)
        sleep(0.1)
        keyboard.press_and_release('enter')
        sleep(0.1)


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


def generate_node(x, y, z, first_wait, second_wait, angles):
    """
    Generate a node using the coordinates and angles. Take in the
    Minecraft RCON object, the coordinates, the primary and secondary
    wait times, and the player object.
    The 5th parameter is the x-rotation angle (-90 = east, 0=south, 90=west...)
    The 6th parameter is the y-rotation angle, ie the vertical angle :
        -90.0 for straight up to 90.0 for straight down
    (see : https://gaming.stackexchange.com/a/200797)
    """
    
    if angles:
        send_cmd([" ".join([str(i) for i in ["/tp @p", x, y, z, 0, 20]])])
        sleep(first_wait)
        send_cmd([" ".join([str(i) for i in ["/tp @p", x, y, z, -90, 20]])])
        sleep(second_wait)
        send_cmd([" ".join([str(i) for i in ["/tp @p", x, y, z, 180, 20]])])
        sleep(second_wait)
        send_cmd([" ".join([str(i) for i in ["/tp @p", x, y, z, 90, 20]])])
        sleep(second_wait)
    else:
        send_cmd([" ".join([str(i) for i in ["/tp @p", x, y, z]])])
        sleep(first_wait+(second_wait*3))


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


def set_gamerules(end=False):
    """
    Function used to set gamerules that could change the world
    when loaded. Stopped at the beginning, started at the end.
    """
    if end:
        cmds = ["/gamerule doDaylightCycle true",
                "/gamerule doWeatherCycle true",
                "/gamerule doFireTick true"]
    else:
        cmds = ["/gamerule doDaylightCycle false",
                "/gamerule doWeatherCycle false",
                "/gamerule doFireTick false"]

    return send_cmd(cmds)


def main(config):
    """
    The main function is used to read config, start
    up the MCRcon connection as well as to iterate
    between all the positions and save those to a file.
    """
    last_tp, save_file = read_last_tp(config)

    print("The program will execute now. You will not be able to use your "
          "computer while the program is executing. It is recommended that "
          "you unplug your keyboard and mouse once the program has started. "
          "If you wish to stop the program, return to the terminal and press "
          "'Ctrl + c'.")

    input("Press enter to start...")
    print("Please place the focus of your system into the minecraft world \n "
          "Starting in 10 seconds...")
    sleep(10)

    radius = int(config['PARAMETERS']['radius'])
    increments = int(config['PARAMETERS']['increments'])
    y = int(config['PARAMETERS']['altitude'])
    first_wait = int(config['PARAMETERS']['first_wait'])
    second_wait = int(config['PARAMETERS']['second_wait'])
    gamerules = str2bool(config['PARAMETERS']['gamerules'])
    x_center = config['PARAMETERS']['x_center']
    z_center = config['PARAMETERS']['z_center']
    creative_true = str2bool(config['PARAMETERS']['creative'])
    angles = str2bool(config['PARAMETERS']['angle'])

    # Set gamerules if activated in the parameters
    if gamerules:
        set_gamerules()

    # Set player in spectator mode just in case
    if creative_true:
        creative = "creative"
    else:
        creative = "spectator"
    send_cmd(["/gamemode " + creative + " @p"])

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
            actual_x = int(x * increments) + int(x_center)
            actual_z = int(z * increments) + int(z_center)
            generate_node(actual_x,
                          y,
                          actual_z,
                          first_wait,
                          second_wait,
                          angles
                          )

            with open(save_file, 'w') as f:
                # Write position and next step to file
                f.write("{0},{1},{2},{3},{4}\n".format(x, z, dx, dz, iterator))

            remaining_time = calculate_time_remaining(iterator,
                                                      normalized_nodes,
                                                      first_wait,
                                                      second_wait)

            print("Player teleported to position:",
                  str(actual_x),
                  str(y),
                  str(actual_z))
            print("Player teleported to normalized position:", x, z)
            print("{0}/{1} nodes completed. {2} left."
                  .format(iterator, normalized_nodes,
                          (normalized_nodes - iterator)))
            print("Approximate remaining time:", remaining_time)

            if x == z or (x < 0 and x == -z) or (x > 0 and x == 1-z):
                dx, dz = -dz, dx

            x, z = x+dx, z+dz

        iterator += 1

    # Unset gamerules
    if gamerules:
        set_gamerules(True)

    print("All finished!")


if __name__ == '__main__':
    config = configparser.ConfigParser()
    config.read("config.ini")

    try:
        main(config)
    # Exit if Ctrl+C or Del is pressed
    except KeyboardInterrupt:
        print("\nExiting...")
        exit(0)