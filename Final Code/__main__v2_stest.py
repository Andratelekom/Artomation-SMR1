# main.py
from DRCF import *
import powerup.checkapp as checkapp
import powerup.motion as motion
#notes
#trans for X movement
#addto for J movement
#print(f" ....{...}") works on local pc for debugging, not on robot. comment out de print(f...) if you want to run the script on the robot.
#HMI language thingey: 0 = "YES" and 1 = "NO"

onward = False
emergency = False

checkapp.hmi_init("Pizza", hub_serial="b8-27-eb-9a-40-89")
checkapp.wait_hmi()

# Global variables
Currentcrates = 0
Currentcrates = int(Currentcrates)

#global speed variables, GET OVERWRTTEN AT setupmovement.
vl = 100  # Linear speed            #current max = 200
al = 100  # Linear acceleration     #current max = 200
vj = 100  # Joint speed             #current max = 200
aj = 100  # Joint acceleration      #current max = 200

#Movement speeds in time per second.
Sslow = 1.5
slow = 1
med = 0.7
smed = 0.6
fast = 0.5
sfast = 0.4

global buffer
rx_msg = "0"

sock = client_socket_open("192.168.123.200", 20002) #if no camera, comment this or it breaks for some reason

#Sub functional calls, uses virtual enviroment
def defaultpos():
    # Home position.
    home_pos = posj(0, 0, 0, 0, 0, 0)
    movej(home_pos, v=100, a=100)       #current max = 100
    return True

def setupmovement():
    # Global variables.
    global vl
    vl = 100  # Linear speed.           #current max = 200
    global al
    al = 100  # Linear acceleration.    #current max = 200
    global vj
    vj = 50  # Joint speed.            #current max = 200
    global aj
    aj = 70  # Joint acceleration.     #current max = 200
    global vl1
    vl1 = 100
    global vl2
    vl2 = 100
    return True


def heightindicator():
    global Currentcrates
    global z_start
    global z_end
    z_start = 80 + (76 * Currentcrates)
    z_end = 132 + (76*-Currentcrates)
    return True

def request():
    global rx_msg
    while sock:
        msg = "Robot is ready!"
        client_socket_write(sock, msg.encode())  # request data from camera

        res, rx_data = client_socket_read(sock)  # receive data from camera

        if rx_data is not None:
            rx_msg = rx_data.decode()  # decode data from camera
            tp_log("{0}".format(rx_msg))  # log the received message
            return rx_msg
        else:
            tp_log("Error: Received None data from socket.")  # Log the error

            return None

def request2():
    global rx_msg2
    global buffer
    while sock:
        msg = "Robot is ready!"
        client_socket_write(sock, msg.encode())  # request data from camera

        res, rx_data = client_socket_read(sock)  # receive data from camera

        if rx_data is not None:
            rx_msg2 = rx_data.decode()  # decode data from camera
            tp_log("{0}".format(rx_msg2))
            if rx_msg2 == "3":
                buffer = rx_msg2# log the received message
                return rx_msg2
        else:
            tp_log("Error: Received None data from socket.")  # Log the error

            return None


def manualremoval():
    # Something went wrong, crate has to be removed manually by user.
    tp_popup("Please remove the crate from the robot.", DR_PM_MESSAGE)  # Send a message to the HMI.
    tp_popup("Crate placed back to stack?", DR_PM_MESSAGE)  # Send a message to the HMI.
    return start_sensor()  # Return to crate loop from start.

#End of Sub functional calls


#Functional calls in order of main program, uses actuators
def start_sensor():
    def checkpickup():  # Function to check if there are crates at the pickup point.

        set_digital_output(1, ON)
        wait(0.1)
        print("Checkpickup running.")
        in1 = get_digital_input(1)
        if in1 == 1:  # If IR_sensor 1 detects something, then continue to checkdropoff.
            return True
        else:  # If IR_sensor 1 detects nothing, no crates are placed.
            pickup_input = checkapp.hmi_yes_no_user_input(title="Please place crates at pickup", message="place pickup crates", yes="YES",no="NO")  # Send a message to the HMI.
            if pickup_input == 1:
                checkapp.hmi_yes_no_user_input(title="Reset",message="The robot will return to home position", yes="YES")
                startup()
            return checkpickup()  # Return to check if IR_sensor 1 detects something.

    def checkdropoff():  # Function to check if there is a rolly at the dropoff point.
        print("Checkdropoff running.")
        in2 = get_digital_input(2)
        if in2 == 1:  # If IR_sensor 2 detects something, then continue to the robot program.
            # Call for robot script or start of functions
            #set_digital_output(1, OFF)
            return True
        else:  # If no rolly is detected
            dropoff_input = checkapp.hmi_yes_no_user_input(title="Please place rolly at dropoff",message="place dropoff rolly", yes="YES",no="NO")  # Send a message to the HMI.
            if dropoff_input == 1:
                return False
            # Send a message to the HMI.
            return checkdropoff()  # Return to check if IR_sensor 2 detects something.

    if checkpickup() and checkdropoff():
        # Both pickup and dropoff are ready, return control to main.py
        return True

def check_emergency():
    global emergency
    if emergency:
        print("Emergency detected. Returning to the beginning.")
        stop(1)
        checkapp.hmi_yes_no_user_input(title="warning", message="The robot will returns to home position", yes="OK")
        emergency = False
        startup()
        return True  # Indicate that an emergency has occurred
    return False

def requestnumbercrates():
    global Currentcrates
    Currentcrates = checkapp.hmi_user_input(title="Please enter the amount of crates at pickup.", value="0",type=DR_VAR_INT)
    if Currentcrates <= 0:  # !!! Crashes program, fix later.
        print("Please enter a number above 0.")
        return requestnumbercrates()
    #elif Currentcrates == "0":
    else:
        return Currentcrates

def safetypos1():
    global Sslow
    # Safety position 1 for pick up.
    int_posj = posj(0.0, -19.8, 122.7, -0.0, -11.0, -90.0)
    movej(int_posj, t=1.5)

    return True

def safetypos1startup():
    global med
    # Safety position 1 for pick up.
    int_posj = posj(0.0, -19.8, 122.7, -0.0, -11.0, -90.0)
    movej(int_posj, t=1.5) #med
    return True

def approachcrate():
    # Approach crate.
    global fast
    global z_start
    global q1

    q1 = posx(487, -3, z_start, 179.4, -92, 91)
    movel(q1, t=0.5)   #fast
    return True

def moveincrate():
    global q2
    global q3
    global q4
    global q5
    global smed

    q2 = trans(q1, posx(37, 0, 0, 0, 0, 0))  # pick up x-axis movemen
    q3 = trans(q2, posx(-1.3, 0.1, -14.3, 0, 6.5, 0))  # pick up joint_5 movement
    q4 = trans(q2, posx(0, 0, -32, 0, 0, 0))  # pick up stabling(joint_5) crate movement
      # pick up gripping(z-axis) movement
    q2_3_4 = [q2, q3, q4]
    movesx(q2_3_4, t=1)

    #smed
    return True

def lockcrate():
    global q5
    global sfast
    q5 = trans(q4, posx(-0.2, 0.1, 13.3, 0, -6, 0)) # lockcrate_3
    movel(q5, t=0.5) #sfast
    return True

def safetypos2():
    # Safety position 2 to prevent crash with other crates and ready to make take pizza pose.
    global q6
    global q5
    global fast
    q6 = trans(q5, posx(0, 0, 100, 0, 0, 0))
    movel(q6, t=0.5)    #fast
    return True

def beltturn(): #beltturn + approach belt + closebelt +pizza1
    global sfast
    q7 = addto(get_current_posj(), [-53.7, 0, 0, 0, 0, 0])  # safety position 2_2
    q8 = posj(-53.7, 33.2, 105.5, 42.7, -66.3, -113.6)  # holding approach belt
    q9 = posj(-59.7, 78.3, 78.1, 33.2, -78.3, -99.5)  # approaching belt z-axis
    q7_8_9 = [q7, q8, q9]

    movesj(q7_8_9, t=0.3)
    return True


    #sfast


def camera1():
    global rx_msg
    request()

    if rx_msg == "1":
        return True
    else:
        while rx_msg != "1":
            request()
            if rx_msg == "1":
                return True
            else:
                wait(0.3)
                request()
                print("Error: Pizza 1 not in crate. Check if stuck.")

def bufferrdy():
    global rx_msg2
    global buffer
    request2()

    if buffer == "3":
        set_digital_output(3, OFF)
        return True
    else:
        while buffer != "3":
            request2()
            if buffer == "3":
                set_digital_output(3, OFF)
                return True
            else:
                wait(0.1)
                request2()
                print("Error: No Pizza in buffer.")

def pizza2(): #pizza 2
    global q10
    global q11
    global hold_app
    global slow
    hold_app = posx(270.7, -598.2, -79.8, 87.5, -81.8, 91.8)
    # approaching pizza pose2 (x-axis)
    q10 = trans(hold_app, posx(-230, 0, -70, 0, 0, 0))
    q11 = trans(q10, posx(0, -130, 0, 0, 0, 0))
    q10_11 = [q10, q11]
    movesx(q10_11, t=1)

    return True

def pizzapullback():
    global q11
    wait(1)
    q12 = trans(q11, posx(0, 100, 0, 0, 0, 0))
    movel(q12, t=0.6)
    return True

def camera2():
    global rx_msg
    global buffer
    request()
    tp_log("{0}".format(rx_msg))  # turn into variable
    if rx_msg == "2":
        return True
    else:
        while rx_msg != "2":
            request()
            #shake()  # Needs to be editted to only happen if pizza is stuck !!!
            if rx_msg == "2":
                set_digital_output(2, ON)
                return True
            else:
                wait(0.1)
                request()
                #shake()
                print("Error: Pizza 1 not in crate. Check if stuck.")

def safetypos3(): #safety3 and set dropoff point
    global q12
    global q13
    global q14
    global smed
    q12 = posj(-67.4, 83.9, 96.6, 25.2, -98.6, -88.0)
    q13 = posj(-67.4, 62.2, 111.3, 24.9, -92.2, -91.0)
    q14 = posj(-66.6, 39.3, 89.2, 100.9, -108.0, -138.3)

    q12_13_14 = [q12, q13, q14]
    movesj(q12_13_14, t=0.4)
    #smed
    return True

def approachdropoff(): #approach dropoff z
    global q15
    global dropoff_pos
    global z_end
    global smed
    dropoff_pos = posx(-400.0, -507.3, 0.0, 2.6, -87.0, 92.0)

    # approaching (z movement)
    q15 = trans(dropoff_pos, posx(0, 0, z_end, 0, 0, 0))
    movel(q15, t=1)

    return True

def lockopen(): #lock open
    global q15
    global q18
    global med
    # place to dropoff
    q16 = trans(q15, posx(0, 0, -28, 0, 0, 0)) # grip lock open
    q17 = trans(q16, posx(0, 0, 0, 0, -5, 0)) # deapproach position (z and x move)
    q18 = q15
    q16_17_18 = [q16, q17, q18]
    movesx(q16_17_18, t=0.7)
    #med
    return True

def withdrawarm(): #withdrawarm z + x
    global q19
    global med

    q19 = trans(q18, posx(50, 0, 0, 0, 0, 0))
    movel(q19, t=0.5)
    return True

# Main
def startup():
    global Currentcrates
    if check_emergency():
        startup()
    if setupmovement():
        print("Initialising svc complete. Proceeding with the main program.") # Initialise speed, velocity and amount of crates (svc).
        # Go to default position.

    if defaultpos():
        # Confirm robot movement.
        print("Robot in position. Proceeding with the main program.")
    # ------------Step 1 Amount of crates------------
        requestnumbercrates() #moved this with tab
        main_program()        #moved this with tab

def main_program():
    global Currentcrates
    global z_end
    global emergency
    while Currentcrates > 0:
        if check_emergency():
            startup()
        if safetypos1startup():
            print("Starting up moving to safetypos1.")
        # ------------Step 2 Senors------------ Also Loop Start-------
        if start_sensor():  # If sensorcheck has passed:
            print("Sensors ready. Calculating Height.")
            set_digital_output(3, ON)  # closes buffer
            # Start robot calculate height.
        # ------------Step 3 Calculate Height------------
        if heightindicator():  # If heightindicator is done:
            print("Height calculated. Moving to safety1.")
        # ------------Step 4 Pickup------------
        if safetypos1():  # If at safety1.
            print("At safety1. Moving to crates.")
            # Go to crate.

        if approachcrate():  # If at crate.
            print("At crates. Moving to enter crates.")
        # ------------Step 5 Grab------------

        if moveincrate():  # If moved into crate.
            print("At crates. Moving to lock.")

        if lockcrate():
            print("Crate locked. Moving to safety2.")

        if safetypos2():  # If crate has been lifted.
            print("Crate moved to safetypos 2. Turning to belt.")
        # ------------Step 6 Belt------------

        if beltturn():  # If crate has been lifted.
            print("Turned to belt. Approaching belt.")
            set_digital_output(3, OFF)  # Opens buffer
        # ------------Step 7 camera 1------------
            #wait(2)
        if camera1():  # If crate has been moved close to the belt
           print("Pizza 1 in crate. Moving for pizza2.")
           set_digital_output(3, ON)
        if pizza2():  # If crate moved to pizza2
            print("At pizza2.")

        # ------------Step 8 camera 2------------
        if bufferrdy():
            print("Pizza in buffer")
            set_digital_output(3, OFF)

        if pizzapullback():
            print("At pizzapullback. Waiting for camera2.")

        if camera2():  # If crate has been moved close to the belt
            print("Pizza 2 in crate. Moving to safety3.")
            set_digital_output(3, ON)  # closes buffer

        if safetypos3():
            print("At safety3. Moving to dropoff")

        if approachdropoff():  # If crate has been moved close to the belt
            print("crate at dropoff. Unlocking crate.")

        if lockopen():
            print("Unlocked crate. Withdrawing arm.")

        if withdrawarm():  # If crate has been moved close to the belt
            print("crate dropped off.")
            Currentcrates = (Currentcrates-1)
            if Currentcrates < 1:
                finished = checkapp.hmi_yes_no_user_input(title="Finished",message="Cycle finished, return to home position", yes="YES",no="NO") # Send a message to the HMI.
                if finished == 0:
                    safetypos1startup()
                    # Confirm robot movement.
                    break
            else:
                if safetypos1():  # If at safety1.
                    print("At safety1. Moving to crates.")
                    # Go to crate.
                    start_sensor()

    # Continue with the rest of the main program


while True:
    if check_emergency():  # Check for emergency at the start of each loop
        motion.stop_motion()
        startup()  # Restart the program if emergency is detected
        emergency = False
        continue  # Go back to the start of the loop

    if onward is True:
        startup()  # Starts the program.
        onward = False
# Starts the program.
