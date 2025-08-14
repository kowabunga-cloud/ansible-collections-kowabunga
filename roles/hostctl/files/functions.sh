#!/bin/bash

#===================================================================================
#
# FILE: functions.sh
#
# DESCRIPTION: The aim of this script is to propose a framework and facilities for shell scripts.
# FUNCTIONS:
# * Display functions
#   - displayServerDetails      Display some info on the server
#   - displaySuccess            Display like TEXT   [  OK  ]
#   - displaySkipped            Display only if verbose like TEXT   [SKIPPED]
#   - displayWarning            Display like TEXT   [ WARN ]
#   - displayFailed             Display like TEXT   [FAILED]
#   - echoTextAndVerdict        Display like TEXT   [VERDICT] with custom color
#   - displayVerbose            Display TEXT only if verbose
#   - storeAndDisplay           Display TEXT and store for failed message
#   - storeAndDisplayFailed     Display and store for failed message like TEXT   [FAILED]
#   - storeAndDisplayWarning    Display and store for failed message like TEXT   [ WARN ]
#   - syslogInfo                Logs an info message to host's syslog
#   - syslogWarning             Logs a warning message to host's syslog
#   - syslogAlert               Logs an alert message to host's syslog
#   - logErrorWithDiagnosis     Display and store error and additional comments, increment error counter
#   - underlined  		Underlined TEXT
#   - linkify  			Underlined blue TEXT
#   - colored  			Colored TEXT
#   - startColor  		Start colored TEXT
#   - endColor  		Reset formatting
#   - displaySection		Display like =            TEXT              = between 2 full ========= lines
#   - displayTitle		Display like ============ TEXT ==============
#   - progressBar		Display or update a progress bar like =--
#   - progressBarStop		Erases he progress bar displayed on current line
#   - showKeyVal		Display in column mode like key:     val
# * Check specific functions
#   - testPromptAndFix          Test, and if failing, prompt the admin and fixes the issue
#   - exitIfNotRoot	        Exits the script if not launched as root
#   - addToArchive		Add file or folder to generated archive
#   - startScript		To call at beginning of your script (load vars, exit if already running...)
#   - endScript		        To call at the end of your script (archive generation, count & list errors, clean working files...)
# * Versions comparison functions
#   - versionBelow		Test if version A is strictly below version B
#   - versionAbove		Test if version A is equal or above version B
#   - versionBetween		Test if version A is strictly below version B and is equal or above version C
# * Misc functions
#   - validIPAddress		Test if parameter is a valid IP address
#   - validFQDN			Test if parameter is a valid FQDN
#   - removeColors		Remove colors (ANSI escape characters) from files in parameters
#   - isInteger                 Tests if the param1 is an integer or not
# OPTIONS: see function 'defaultUsage' below
#
#===================================================================================

#===================================================================================
# Vars/constants Declaration
#===================================================================================

# Script important vars declaration
declare -r scriptName=`basename $0`		# Scripts name, used in usage and working files names
declare -r originDirectory=`pwd`		# originale directory, stored to go back at the end
errors=0								# counter for errors found by script

# script behaviour initialization
isDisplayOnly=0	# activates the display mode, with no files storage on the host. values: 0, 1 ; default: 0
isQuietMode=0	# activates the quiet mode, with no output on console. values: 0, 1 ; default: 0
isVerbose=0	# activates the verbose mode, with more output in console like skipped tests. values: 0, 1 ; default: 0
BOOTUP=nocolor	# choose if you want colors or not on console, with no files storage on the host. values: nocolor, color ; default: color
isInteractive=0 # by default, do not prompt the user
isForce=0       # some options may require the --force option to be added to be sure this is not an error or skip interactive mode

# Exit code declaration
declare -r errorCallParameters=101	# unknown parameters
declare -r errorAlreadyRunning=102	# the script can run only once at a time on a host
declare -r errorNotRoot=103		# the script can be executed only by root
declare -r errorInternalScriptError=104	# The script failed (eg: could not access other mandatory files)
declare -r errorWrongEnvironment=105 	# if the script is launched on non supported host

# script working files declaration
declare -r hostname=`hostname -s`
declare -r currentDate=`date "+%Y%m%d-%H%M%S"`
declare -r scriptRootName=$(basename $0 .sh)
declare -r workingDir="/tmp/${scriptRootName}"
[ ! -z ${workingDir} ] && mkdir -p -m 777 "${workingDir}"
declare -r scriptOutFile="${workingDir}/${scriptRootName}-${hostname}-${currentDate}.log"
declare -r scriptErrFile="${workingDir}/${scriptRootName}.error.log"
declare -r scriptMoreFile="${workingDir}/${scriptRootName}.more.log"
declare -r scriptFailFile="${workingDir}/${scriptRootName}.failed.log"
declare -r scriptOutPipe="${workingDir}/${scriptRootName}.out.pipe"
declare -r scriptErrPipe="${workingDir}/${scriptRootName}.err.pipe"
declare -r scriptLockFile="/var/run/${scriptRootName}.pid"

# display vars declaration
declare -r valColumnStart=15	# The left space length before showing the command alias
columns=$(stty size | cut -d ' ' -f 2)
if [ ${columns} -gt 80 ]; then
                                # The left space length before showing the [VERDICT]
    declare -r verdictColumn=$((${columns}-12))
else
    declare -r verdictColumn=65	# The left space length before showing the [VERDICT]
fi
declare -r titleLineLen=80	# The size of the title and section text
declare -r titleSep="="		# The character used to emboss title and section text
declare -r colorRed=31
declare -r colorGreen=32
declare -r colorOrange=33
declare -r colorBlue=34
declare -r colorMagenta=35
declare -r colorCyan=36

# Copy this function to your own script, adapt it to your needs & rename it usage()
defaultUsage() {
    echo "Usage: ${scriptName} Options"
    echo 'The aim of this script ...'
    echo
    echo 'Options:'
    echo '  -d, --display: Execute the script without storing any file'
    echo '  -h, --help:    Shows this script help'
    echo '  -c, --color:   The output is human readable, with colors/formating characters'
    echo '  -ni, --non-interactive, CHECKONLY: '
    echo '     The user will not be prompted for input, like yes/no questions'
    echo "     Tools' behaviour in this case will depend on tool, awaited input and other options"
    echo '  -q, --quiet:   All info from STDOUT and STDERR will be redirected to logs, and console will remain empty'
    echo '  -V, --verbose: Shows more output in the console (skipped tests...)'
    echo
}
# loadOptions function can be created in xxxx script for a specific options management

#===================================================================================
# Display functions
#===================================================================================

# human readable elapsed time
# eg:
#      lastLogRotation=$(stat -c '%Y' /var/log/syslog 2>/dev/null)
#      elapsedSeconds=$(( $(date +%s) - ${lastLogRotation} ))
#      echo $(formatSeconds ${elapsedSeconds})
function formatSeconds() {
    (($1 >= 86400)) && printf '%d days ' $(($1 / 86400))      # days
    (($1 >= 3600)) && printf '%02d:' $(($1 / 3600 % 24))      # hours
    (($1 >= 60)) && printf '%02d:' $(($1 / 60 % 60))          # minutes
    printf '%02d%s\n' $(($1 % 60)) "$( (($1 < 60 )) && echo ' s.' || echo '')"
}

# displayServerDetails displays host type, host version and hardware
displayServerDetails() {
    displaySection "Server details"
    showKeyVal hostname ${hostname}
}

# displaySuccess writes a text ($1) with an [ OK ] in green on the right of the screen
# If the $1 text is too long, the [ OK ] is displayed on next line
#   Param $1: The text to display before the verdict
displaySuccess() {
    local text="$1"
    echoTextAndVerdict "${text}" "  OK  " $colorGreen
}

# displaySkipped writes a text ($1) with an [SKIPPED] in orange on the right of the screen
# If the $1 text is too long, the [SKIPPED] is displayed on next line
# The function exits with no output if isVerbose=0
#   Param $1: The text to display before the verdict
displaySkipped() {
    [ ${isVerbose} = 0 ] && return
    local text="$1"
    echoTextAndVerdict "${text}" "SKIPPED" $colorOrange
}

# displayWarning writes a text ($1) with an [ WARNING ] in orange on the right of the screen
# If the $1 text is too long, the [ OK ] is displayed on next line
#   Param $1: The text to display before the verdict
displayWarning() {
    local text="$1"
    echoTextAndVerdict "${text}" " WARN " $colorOrange
}

# displayFailed writes a text ($1) with an [ FAILED ] in red on the right of the screen
# If the $1 text is too long, the [FAILED] is displayed on next line
#   Param $1: The text to display before the verdict
displayFailed() {
    local text="$1"
    echoTextAndVerdict "${text}" "FAILED" $colorRed
}

# displayVerbose writes a text ($1) to console only if script is launched in verbose mode
#   Param $1: The text to display
displayVerbose() {
    local text="$1"
    [ ${isVerbose} = 0 ] && return
    echo -e "${text}"
}

# storeXxxxx functions are used to store the text in a file and present it again at the end
# and on all shell sessions using wall command
#   Param $@: The text to store in $scriptFailFile
store() {
    local text="$@"
    echo "${text}" >> ${scriptFailFile}
}

# used to display a message and store it for later use
#   Param $@: The text to display and store in $scriptFailFile
storeAndDisplay() {
    local text="$@"
    echo "${text}"
    store "${text}"
}

# used to display a message with [FAILED] and store it for later use
#   Param $1: The text to display and store in $scriptFailFile with [FAILED] verdict
storeAndDisplayFailed() {
    local text="$1"
    store "[FAILED] ${text}"
    displayFailed "${text}"
}

# used to display a message with [ WARN ] and store it for later use
#   Param $1: The text to display and store in $scriptFailFile with [ WARN ] verdict
storeAndDisplayWarning() {
    local text="$1"
    store "[ WARN ] ${text}"
    displayWarning "${text}"
}

# To log a message to host's syslog (user.info facility)
#   Param $1: The message to log
syslogInfo() {
    syslog info "$1"
}

# To log a warning to host's syslog (user.warning facility)
#   Param $1: The alert to log
syslogWarning() {
    syslog warning "$1"
}

# To log an alert to host's syslog (user.alert facility)
#   Param $1: The alert to log
syslogAlert() {
    syslog alert "$1"
}

# To log a message to host's syslog (user.xxx facility)
#   Param $1: The alert to log
# where severity is one of: debug info notice warning err crit alert emerg
syslog() {
    logger -t ${scriptName} -p user."$1" "$2"

}

# displays a message with [ FAILED ] verdict and stores it in $scriptFailFile.
# displays additional arguments and stores them in $scriptFailFile.
# increments the error count.
#   Param $1: The verdict
#   Additional Param: additional arguments to be displayed and stored.
logErrorWithDiagnosis() {
    storeAndDisplayFailed "${1}"
    shift
    while [ $# -gt 0 ];	do
	storeAndDisplay "${1}"
	shift
    done
    ((errors++))
}

# underlined writes a text ($1) underlined with a CR at the end
#   Param $1: The text to display underlined
underlined() {
    local text="$1"
    [ "$BOOTUP" = "color" ] && echo -en "\033[4m"
    echo -en "${text}"
    [ "$BOOTUP" = "color" ] && echo -en "\033[0m"
    echo -en "\n"
}

# linkify writes a text ($1) underlined and blue without CR at the end
#   Param $1: The text to display underlined and blue
linkify() {
    local text="$1"
    [ "$BOOTUP" = "color" ] && echo -en "\033[4;1;${colorBlue}m"
    echo -en "${text}"
    [ "$BOOTUP" = "color" ] && echo -en "\033[0;39m"
}

# colored writes a text ($1) colored with color $2 and a CR at the end
#   Param $1: The text to display colored
#   Param $2: The color (integer). can be one of $colorRed, $colorGreen...
colored() {
    local text="$1"
    local color="$2"
    startColor "${color}"
    echo -en "${text}"
    endColor
    echo -en "\n"
}

# Echoes the charaters to color the text displayed later.
# To use with endColor
#   Param $1: The color (integer). can be one of $colorRed, $colorGreen...
startColor() {
    local color="$1"
    [ "$BOOTUP" = "color" ] && echo -en "\033[1;${color}m"
}

# Echoes the charaters to stop coloring the text displayed later.
# To use with startColor
endColor() {
    [ "$BOOTUP" = "color" ] && echo -en "\033[0;39m"
}

# displaySection writes a text ($1) between 2 lines of hash
#   Param $1: The text to display as section
displaySection() {
    displayTitle
    displayTitle "$1" "spaces"
    displayTitle
}

# displayTitle writes a text ($1) with = at the begining
#   Param $1: The text to display as title
#   Param $2: The type of display (empty or 'spaces')
#             If empty, the title will be like    ======== title =========
#             If 'spaces', the title will be like =        title         =
displayTitle() {
    text="$1"
    format="$2"
    if [ ${#text} = 0 ] ; then
	tmpStr=$(printf "%${titleLineLen}s")
	sepStr=${tmpStr// /"${titleSep}"}
	echo "${sepStr}"
    elif [ "${format}" = "spaces" ] ; then
	sepLen=$(((${titleLineLen}-${#text}-4)/2))
	[ ${sepLen} -lt 1 ] && sepLen=1
	tmpStr=$(printf "%${sepLen}s")
	sepStr=${tmpStr// /" "}
	finalStr="${sepStr} ${text} ${sepStr}"
	[ ${#finalStr} -lt $((${titleLineLen}-2)) ] && finalStr="${finalStr} "
	echo "${titleSep}${finalStr}${titleSep}"
    else
	sepLen=$(((${titleLineLen}-${#text}-2)/2))
	[ ${sepLen} -lt 1 ] && sepLen=1
	tmpStr=$(printf "%${sepLen}s")
	sepStr=${tmpStr// /"${titleSep}"}
	finalStr="${sepStr} ${text} ${sepStr}"
	[ ${#finalStr} -lt ${titleLineLen} ] && finalStr="${titleSep}${finalStr}"
	echo "${finalStr}"
    fi
}

# echoTextAndVerdict displays a line with a text and a colored verdict on the right
# with colors like:
# Text                          [VERDICT]
# without colors, like:
# [VERDICT] Text
#   Param $1: is the text
#   Param $2: is the verdict text. take care of rigth spaces for the verdict like: "  OK  "
#   Param $3: The color (integer). can be one of $colorRed, $colorGreen...
echoTextAndVerdict() {
    local text="$1"
    local verdict="$2"
    local color="$3"
    if [ "$BOOTUP" = "color" ] ; then
	[ "${#text}" -lt $verdictColumn ] && echo -n "${text}" || echo "${text} "
	echo -en "\\033[${verdictColumn}G[\\033[1;${color}m${verdict}\\033[0;39m]\n"
    else
	echo -e "[${verdict}] ${text}"
    fi
}

# displays a progress bar caption and prepares the next progress bar.
#   call progressBar each time you want to start or update the progress bar for instance,
#     in a while loop with sleep inside
#   call progressBarStop to erase the progress bar
progressBarNext="0"
progressBar() {
    if [ "$BOOTUP" = "color" ]; then
	case "${progressBarNext}"
	in
	    1)
		echo -ne "\\010\\010\\010\\010\\010 =-- "
		progressBarNext="2"
		;;
	    2)
		echo -ne "\\010\\010\\010\\010\\010 -=- "
		progressBarNext="3"
		;;
	    3)
		echo -ne "\\010\\010\\010\\010\\010 --= "
		progressBarNext="4"
		;;
	    4)
		echo -ne "\\010\\010\\010\\010\\010 --- "
		progressBarNext="1"
		;;
	    *)
		echo -ne " --- "
		progressBarNext="1"
		;;
	esac
    fi
}

# See progressBar
progressBarStop() {
    if [ "$BOOTUP" = "color" ] && [ ! "${progressBarNext}" = "0" ] ; then
	echo -ne "\\010\\010\\010\\010\\010     \\010\\010\\010\\010\\010"
	progressBarNext="0"
    fi
}

# Prints a key and a value seperated in column mode like:
# key:         value
# where key is bolded
#   Param $1: the key to display
#   Param $2: the value to display
showKeyVal() {
    local key="$1"
    local val="$2"
    local spaces=`expr ${valColumnStart} - ${#key}`
    if [ "$BOOTUP" = "color" ]; then
	printf "\033[1;${colorOrange}m%-${valColumnStart}s\033[0;39m%s\n" " ${key}:" " ${val}"
	#printf "\033[1;${colorOrange}m%s\033[0;39m%-${spaces}s %s\n" "${key}" ":" "${val}"
    else
	printf "%s%-${spaces}s %s\n" "${key}" ":" "${val}"
    fi
}

#===================================================================================
# Internal/private functions
#===================================================================================

# Deletes pipe and working files
# This function is automatically launched during startCheckScript & endCheckScript.
cleanWorkFiles() {
    rm -f ${scriptFailFile} ${scriptErrFile} ${scriptMoreFile} ${scriptOutFile} ${scriptOutPipe} ${scriptErrPipe} >/dev/null
    #displayVerbose "  > Working files cleaned: ${scriptFailFile} ${scriptErrFile} ${scriptMoreFile} ${scriptOutFile} ${scriptOutPipe} ${scriptErrPipe}"
}

# loadHostInfos creates and archive at the end of checkXxxx script, with some system files and
# specific files & folders chosen by checkXxxx script using addToArchive function.
# This function is automatically launched during endCheckScript.
createArchive() {
    [ ${isDisplayOnly} = 1 ] && return 0
    echo
    displayTitle "Generation of an archive containing all related logs and files"
    zip -9rq ${scriptArchive} 2>${scriptErrFile} \
	${scriptFailFile} ${scriptErrFile} ${scriptMoreFile} ${scriptOutFile} \
	${ECC_HOME}/version*.txt \
	${ECC_HOME}/topology/topology.xml \
	${ECC_HOME}/ecc.properties \
	${BICS_DATA_HOME}/bics.conf \
	${filesToArchive}

    if [ -e ${scriptArchive} ] ; then
	scriptArchiveSize=`ls -lh ${scriptArchive}|awk '{print $5}'`
	displayTitle "${scriptArchive} (${scriptArchiveSize}) can now be downloaded"
    else
	displayTitle "Oups! ${scriptArchive} does not exist..."
	#exit ${errorInternalScriptError}
    fi
}

# This function initializes the host description vars (hardware...).
# This function is automatically launched during startScript
loadHostInfos() {
    hostHardware=`dmidecode -t 1 | sed -r -n "s|^.*Product Name: (.*)$|\1|p"`
    #myIp=$(ifconfig ${NODE_LAN_ETH}|grep 'inet addr'|awk -F':' '{print $2}' |awk -F' ' '{print $1}')
}

#===================================================================================
# Specific functions to control your own script
#===================================================================================

# Test, and if failing, prompt the admin and fixes the issue
#    Param 1: A string describing the test
#    Param 2: The testFunction name to run
#    Param 3: The fixFunction name to run
#    Param 4: The test & fix functions parameter. May be empty
# testFunction has to return 0 if no issue has been found, 1 if an issue has been detected and present the issue with displayWarning
# test & fix functions parameters:
#    Param 1: A string describing the test
#    Param 2: The testFunction parameter. May be empty
# Return value:
#    0:  OK, no problem
#    1:  OK, the problem has been fixed
#    10: NOK, prompt admin for fix disabled
#    11: NOK, admin answered no
#    12: NOK, test after fix is still NOK
# It's up to the checkScript to use the return value and decide to display and/or store the error and maybe increment the errors counter
testPromptAndFix () {
    local text="$1"
    local testFunction="$2"
    local fixFunction="$3"
    local functionsOption="$4"

    # First run the test and exit if no error
    if ${testFunction} "${text}" "${functionsOption}"; then
	displaySuccess "${text}"
	return 0
    fi

    # Then if interactive mode is disabled exit
    if [ ${isNonInteractive} = 1 ]; then
	displaySkipped "${text}: Auto-fix skipped in non-interactive mode"
	return 10
    fi

    # Then ask the admin if he wants an automatic fix
    colored "Do you want to fix it? (Y/N)" ${colorBlue}
    read
    case ${REPLY} in
	y|yes|Yes|YES|Y)
	    ${fixFunction} "${text}" "${functionsOption}"
	    ;;
	*)
	    displayWarning "${text}: Auto-fix skipped by admin"
	    return 11
	    ;;
    esac

    # Finaly run the test again and exit if no error
    if ${testFunction} "${text}" "${functionsOption}"; then
	displaySuccess "${text}"
	return 1
    fi

    # If the issue is still present, exit
    displayWarning "${text}: Auto-fix failed"
    return 12
}

# Add the files and/or folders given as param to the generated archive of the script
# Archive will be created only at the end of the script if not launched with -d option
addToArchive() {
    local files="$@"
    filesToArchive="${filesToArchive} ${files}"
}

# display the failed tests in red in stderr
#    Param 1: if = "stdout", then will be outputed to stdout instead of stderr
echoFailedTests() {
    startColor $colorRed
    if [ -e ${scriptFailFile} ]; then
	[ "$1" = "stdout" ] && cat ${scriptFailFile} >&1 || cat ${scriptFailFile} >&2
    fi
    endColor
}

# launches everything needed for a starting a custom script:
#  - clears the screen
#  - Exits if the script is already running
#  - Clean working files (console log, tgz...) & Start redirection to log files
#  - Move to temp directoy
#  - Display script name and version
startScript() {
    # clears the screen
    #[ "$BOOTUP" = "color" ] && [ ${isQuietMode} = 0 ] && clear

    #displayVerbose "  > startCheckScript"
    # Exits if the script is already running
    exitIfScriptIsAlreadyRunning

    # Clean working files (console log, tgz...)
    cleanWorkFiles

    # Create the archive of the script, inluding working files and some OT files
    # Also, all files and/or folders selected with createArchive will be archived
    createArchive

    # Start redirection to log files
    if [ ${isDisplayOnly} = 0 ]; then
        if [ ${isQuietMode} = 0 ]; then
            mkfifo ${scriptOutPipe} ${scriptErrPipe}
            tee ${scriptOutFile} < ${scriptOutPipe} >&3 &
            pid_out=$!
            exec 1>${scriptOutPipe}
            tee ${scriptErrFile} < ${scriptErrPipe} >&4 &
            pid_err=$!
            exec 2>${scriptErrPipe}
        else
            exec 1> ${scriptOutFile}
            exec 2> ${scriptErrFile}
    	fi
    fi

    # Move to working directoy
    cd ${workingDir}
    #displayVerbose "  > Moving to workingDir folder"

    loadHostInfos
}

# launches everything needed for an ending a custom script:
#  - Display the number of errors and the stored error logs
#  - Move to origin directoy
#  - End redirection to log files & Clean working files
#  - Remove colors from log file
#  - Create the archive of the script, inluding working files, some OT files, and files and/or folders selected
#  - Exit the script with 0 if no errors how been, found, else with the number of errors (capped to 100)
endScript() {
    #displayVerbose "  > endCheckScript"

    # Display the number of errors
    if [ $errors -gt 100 ]; then
	errors=100
	displayTitle "Potential issue(s): More than 99"
    elif [ ${errors} -ne 0 ]; then
	displayTitle "Potential issue(s): ${errors}"
    fi

    # Display the stored error logs
    echoFailedTests "stdout"

    # Move to origin directoy
    #cd ${originDirectory}
    #displayVerbose "  > Moving to original folder (${originDirectory})"

    # Remove colors from log file
    [ ${isDisplayOnly} = 0 ] && removeColors ${scriptOutFile} ${scriptMoreFile}
    #displayVerbose "  > Removing colors from log files"

    # End redirection to log files
    if [ ${isDisplayOnly} = 0 ]; then
        exec 1>&3 3>&- 2>&4 4>&-
        if [ ${isQuietMode} = 0 ]; then
            wait ${pid_out}
            wait ${pid_err}
        fi
    fi

    # Clean working files
    cleanWorkFiles
    rm -f ${scriptLockFile} >/dev/null

    # Exit the script with 0 if no errors how been, found, else with the number of errors (capped to 100)
    exit ${errors}
}

# the script exits if not launched as root
exitIfNotRoot() {
    local uid=`id -u`
    if [ ${uid} -ne 0 ]; then
	echo
	echo "  /!\ Please run this script as root!"
	echo
	exit ${errorNotRoot}
    fi
    #displayVerbose "  > OK: The script has been launched as root"
}

# the script exits if already running
exitIfScriptIsAlreadyRunning() {
    # Use a lockfile containing the pid of the running process
    # If script crashes and leaves lockfile around, it will have a different pid so
    # will not prevent script running again.
    lf="${scriptLockFile}"
    # create empty lock file if none exists
    sh -c "cat /dev/null >> $lf"
    read lastPID < $lf
    # if lastPID is not null and a process with that pid exists, exit
    if [[ ! -z "$lastPID" ]]; then
	if [[ -d /proc/$lastPID ]]; then
	    echo
	    echo "  /!\ This script is already running."
	    echo "      Please wait for the other instance to be finished (pid=${lastPID})!"
	    echo
	    exit ${errorAlreadyRunning}
	fi
	displayWarning "Another execution of this script has been interrupted or crashed."
    fi
    # save my pid in the lock file
    sh -c "echo $$ > $lf"
    #displayVerbose "  > OK: The script is not already running"
}

#===================================================================================
# Version compare functions
#===================================================================================

# Usage: split "<word list>" <variable1> <variable2>...
# Split a string of $IFS seperated words into individual words, and
# assign them to a list of variables. If there are more words than
# variables then all the remaining words are put in the last variable;
# use a dummy last variable to collect any unwanted words.
# Any variables for which there are no words are cleared.
split() {
    local split_wordlist="${1}"
    shift
    read "$@" <<< "${split_wordlist}"
}

# Usage: version_ge v1 v2
# Where v1 and v2 are multi-part version numbers such as 12.5.67
# Missing .<number>s on the end of a version are treated as .0, & leading
# zeros are not significant, so 1.2 == 1.2.0 == 1.2.0.0 == 01.2 == 1.02
# Returns:
#     0 if v1 = v2
#    10 if v1 > v2
#    20 if v1 < v2
#    11 if v1 { v2 (includes)
#    21 if v1 } v2 (includes)
version_ge() {
    # Prefix local names with the function name to try to avoid conflicts
    # local version_ge_1 version_ge_2 version_ge_a version_ge_b
    # local version_ge_save_ifs
    local version_ge_v1=`echo "${1}" | sed -r 's/[ -]+/./g'`
    local version_ge_v2=`echo "${2}" | sed -r 's/[ -]+/./g'`
    #echo "            ? compare: ${1} and ${2}"
    local version_ge_save_ifs="${IFS}"
    while test -n "${version_ge_v1}${version_ge_v2}"; do
        IFS="."
        split "${version_ge_v1}" version_ge_a version_ge_v1
        split "${version_ge_v2}" version_ge_b version_ge_v2
        IFS="${version_ge_save_ifs}"

	if [ -z "${version_ge_a}" ] && [ ! -z "${version_ge_b}" ]; then
	    #echo "            ? Compare done: ${1} { ${2}"
	    return 21
	elif [ ! -z "${version_ge_a}" ] && [ -z "${version_ge_b}" ]; then
	    #echo "            ? Compare done: ${1} } ${2}"
	    return 11
	fi
	version_ge_a=` echo "${version_ge_a}" | sed -r -n 's|^[0 ]*(.+)$|\1|p'`
	version_ge_b=` echo "${version_ge_b}" | sed -r -n 's|^[0 ]*(.+)$|\1|p'`
	#echo "            ? version_ge_a=${version_ge_a} version_ge_b=${version_ge_b} "
	sortAB=`echo -e "${version_ge_a}\n${version_ge_b}"| sort -n|head -n 1`
	sortBA=`echo -e "${version_ge_b}\n${version_ge_a}"| sort -n|head -n 1`
	#echo "            ? sortAB=${sortAB} sortBA=${sortBA} "
	if [ ! "${version_ge_a}" = "${version_ge_b}" ]; then
	    if [ "${sortBA}" = "${version_ge_a}" ] && [ "${sortAB}" = "${version_ge_a}" ]; then
		#echo "            ? Compare done: ${1} < ${2}"
		return 20
	    fi
	    if [ "${sortBA}" = "${version_ge_b}" ] && [ "${sortAB}" = "${version_ge_b}" ]; then
		#echo "            ? Compare done: ${1} > ${2}"
		return 10
	    fi
	fi

        #test "${version_ge_a}" -gt "${version_ge_b}" && return 10 # v1>v2: true
        #test "${version_ge_a}" -lt "${version_ge_b}" && return 20 # v1<v2:false
    done
    # version strings are both empty & no differences found - must be equal.
    #echo "            ? Compare done: ${1} = ${2}"
    return 0
}

# Tests 2 versions and tells if they match
#
# ${1} is the version you are expecting
# ${2} is the version you have and you hope will match the expected one
# ${3} is the pattern allowed, like =<{ means at least, where:
#    = is the exact same version, like 2.0.5 = 2.000.5
#    < is an newer version, like 2.1 < 2.4
#    > is an older version, like 2.0 > 1.5
#    { is a newer sub version, like 2.0 { 2.0.5
# Examples:
#    testVersionLike "2.0" "2.0.000.020" "}>="
#       returns 0
#       Means is my version at least a 2.0, matches 3.0, but not 1.5
#    testVersionLike "2.0.000.060" "2.0.000.020" "<"
#       returns 0
#       Means is my version older than a 2.0.0.60
function versionLike() {
    local versionTheory=${1}
    local versionReal=${2}
    local versionMatch=${3}

    version_ge "${versionTheory}" "${versionReal}"
    local result=${?}

    comp='e'
    if [ "${result}" = "0" ]; then
	comp='='
    elif [ "${result}" = "10" ]; then
	comp='>'
    elif [ "${result}" = "20" ]; then
	comp='<'
    elif [ "${result}" = "11" ]; then
	comp='}'
    elif [ "${result}" = "21" ]; then
	comp='{'
    fi

    #echo "    versionMatch="${versionMatch}" & result="${comp}
    if [[ "${versionMatch}" = *"${comp}"* ]]; then
	return 0
    fi
    return 1
}

# if ${2} is below (not equal) ${1} (reference version), returns 0, else 1
versionBelow() {
    versionLike "${1}" "${2}" ">"
    local res=${?}
    #[ ${res} = 0 ] && displayVerbose "  > CheckVersion OK: ${2} is below ${1}" || displayVerbose "  > CheckVersion failed: ${2} is  not below ${1}"
    return ${res}
}

# if ${2} is equal or above ${1} (reference version), returns 0, else 1
versionAbove() {
    versionLike "${1}" "${2}" "=<{"
    local res=${?}
    #[ ${res} = 0 ] && displayVerbose "  > CheckVersion OK: ${2} is above ${1}" || displayVerbose "  > CheckVersion failed: ${2} is  not above ${1}"
    return ${res}
}

# if ${3} is equal or above ${1} and ${3} is below ${2}, returns 0, else 1
versionBetween() {
    versionLike "${1}" "${3}" "=<{"
    local res1=${?}
    versionLike "${2}" "${3}" ">"
    local res2=${?}
    #echo '    versionBetween "'${1}'" =<{ "'${3}'" < "'${2}'", result is '${res1}' & '${res2}
    if [ "${res1}" = 0 ] && [ "${res2}" = 0 ]; then
	#displayVerbose "  > CheckVersion OK: ${3} is between ${1} and ${2}"
	return 0
    fi
    #displayVerbose "  > CheckVersion failed: ${3} is not between ${1} and ${2}"
    return 1
}

#===================================================================================
# Misc functions
#===================================================================================

# Analyzes the inputed string and returns 0 if it's a valid IP address, else returns another integer
#   Param $1: The string to analyze
validIPAddress() {
    echo "${1}" | egrep -q "^(((25[0-5]|2[0-4][0-9]|1[0-9]{2}|[1-9]{1}[0-9]|[1-9])\.){1}((25[0-5]|2[0-4][0-9]|[1]{1}[0-9]{2}|[1-9]{1}[0-9]|[0-9])\.){2}((25[0-5]|2[0-4][0-9]|[1]{1}[0-9]{2}|[1-9]{1}[0-9]|[0-9]){1}))$"
}

# Analyzes the inputed string and returns 0 if it's a valid FQDN, else returns another integer
# 0.0.0.0 is not a valid FQDN
#   Param $1: The string to analyze
validFQDN() {
    echo "${1}" | egrep -q "^0+\.0+\.0+\.0+$" && return 1
    echo "${1}" | egrep -q "^([a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?\.)+([a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?\.)+([a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?)$"
}

# Usage : setvar <config_file> <var_name>
# reads the variable <var_name> in <config_file> file and stores it in $var_<var_name> variable
setvar() {
    # $1 file
    # $2 variable
    GREPEXPR="^"$2'='
    VAR=`grep -e $GREPEXPR  $1 2>/dev/null`
    if  [ -n "$VAR" ] ; then
	eval "var_"$VAR
	return 0
    else
	return 1
    fi
}

# Tests if the param1 is an integer and returns 0 if yes, another int if no
isInteger(){
    expr "$1" + 0 >/dev/null;
}

# Remove colors and vertical alignement from log file
#   Params: The files in which all shell colors will be removed
#   Function can be used with more than one file in parameters seperated
#      by a space, and each file will be decolored.
removeColors() {
    while [[ $1 ]]; do
	if [ -f $1 ]; then
	    # Remove colors, underline, bold and cursor horizontal placing
	    sed -i 's/\x1b\[[0-9;]*[mG]//g' $1
	    # interpret backspaces and remove them
	    #sed -i 's/[^\x08\r\n]\?\x08//g' $1
	    while grep -q -U $'\010' $1; do
		sed -i 's/[^\x08\r\n]\?\x08//' $1
	    done
	fi
	shift 1
    done
}

# Prompt the user with Yes/No.
promptYesNo() {
    if [ ${isInteractive} = 0 ] && [ ${isForce} = 0 ]; then
        return 0
    fi
    while true; do
        read -p "Are you sure you want to $1? " yn
        case $yn in
            [Yy]* ) return 0;;
            [Nn]* ) return 1;;
            * ) echo "Please answer yes or no. ";;
        esac
    done
}

#===================================================================================
# Load of script options
#===================================================================================
loadDefaultOptions() {
    #echo "(loadDefaultOptions) received options: $@"
    while [[ $1 ]]; do
	case "$1" in
	    '-?'|'?'|'-h'|'--help')
		usage
		exit 0
		;;
	    '-V'|'--verbose')
		isVerbose=1
		shift 1
		;;
	    '-ni'|'--non-interactive'|'CHECKONLY'|'-I')
		isNonInteractive=1
		shift 1
		;;
	    '-i'|'--interactive')
		isInteractive=1
		shift 1
		;;
	    '-f'|'--force')
		isForce=1
		shift 1
		;;
	    '-d'|'--display')
		isDisplayOnly=1
		shift 1
		;;
	    '-q'|'--quiet')
		isQuietMode=1
		shift 1
		;;
	    '-c'|'--color')
		BOOTUP="color"
		shift 1
		;;
	    -*)
		echo
		echo "  /!\ Error: Unknown option: $1"
		echo
		usage
		exit ${errorCallParameters}
		;;
	    *)  # No more options
		break
		;;
	esac
    done
    #[ ${isVerbose} = 1 ] && displayVerbose "  > Verbose mode:         On" || displayVerbose "  > Verbose mode:         Off"
    #[ ${isDisplayOnly} = 1 ] && displayVerbose "  > Display only mode:    On" || displayVerbose "  > Display only mode:    Off"
    #[ ${BOOTUP} = "color" ] && displayVerbose "  > Color mode:           On" || displayVerbose "  > Color mode:           Off"
}
[ ! -z $(type -t loadOptions) ] && loadOptions $@ || options=$@
loadDefaultOptions ${options}
