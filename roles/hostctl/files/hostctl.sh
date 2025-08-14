#!/bin/bash

declare -r hostModulesPath="/etc/hostctl/modules.d"
declare -r hostModulesPriorityMin=1
declare -r hostModulesPriorityDefault=5
declare -r hostModulesPriorityMax=10

# Test criterias
partionMaxSize=90    # Partition max usage
memPercentMax=90     # Physical memory max usage
fdPercentMax=90      # File descriptors count should not exceed this amount in %
cpuUsageMax=90       # CPU usage max usage

# Some vars
stopServiceTimeout=120          # The max time in seconds to wait after a service stop is requested until it's down
startServiceTimeout=120         # The max time in seconds to wait after a service start is requested until it's up

hostModulesCmdReversePriority=("stop" "stopapp")
hostModules=()                  # Dynamic list of host module extensions

# register custom hostctl modules
registerModules() {
    for mod in ${hostModulesPath}/*; do
        test -f ${mod} && grep -q MOD_NAME ${mod} && source ${mod}
        [ -n "${MOD_PRIO}" ] && prio=${MOD_PRIO} || prio=${hostModulesPriorityDefault}
        local module="${prio}:${MOD_NAME}"
        hostModules=(${hostModules[@]} ${module})
        unset MOD_NAME MOD_PRIO
    done
}

# execute custom hostctl modules
modulesExec() {
    local mod="$1"
    local fct="$2"
    local mod_fct="${mod}_${fct}"
    type ${mod_fct} &>/dev/null && ${mod_fct}
}

modulesCmd() {
    local cmd="$1"
    local OrderAsc=$(seq ${hostModulesPriorityMin} ${hostModulesPriorityMax})
    local OrderDesc=$(seq ${hostModulesPriorityMin} ${hostModulesPriorityMax} | tac)
    cmdOrder=${OrderAsc}
    [[ " ${hostModulesCmdReversePriority[@]} " =~ " ${cmd} " ]] && cmdOrder=${OrderDesc}

    # process all modules commande, per priority first, then per name
    for i in ${cmdOrder}; do
        for m in "${hostModules[@]}"; do
            local mod=($(echo $m | sed 's/:/ /g'))
            local priority=${mod[0]}
            local name=${mod[1]}
            [ ${priority} -eq ${i} ] && modulesExec ${name} ${cmd}
        done
    done
}

# This message will be displayed if the script is called with -h or --help
usage() {
    echo "Usage: ${scriptName} [OPTIONS] [ACTION]"
    echo
    echo 'OPTIONS:'
    echo '  -h, --help:    Shows this script help'
    echo '  -v, --version: Shows the script version'
    echo '  -c, --color:   The output is colors/formating characters free'
    echo '  -q, --quiet:   All info from STDOUT and STDERR will be redirected to logs, and console will remain empty'
    echo '  -V, --verbose: Shows more output in the console (skipped tests...)'
    echo '  -i, --interactive: The admin will be prompt, eg: before performing a restart in prod'
    echo
    echo 'ACTION:'
    echo '  stop:    gentle stop of all host services'
    echo '  start:   start of all host services which are not already started'
    echo '  restart: gentle restart or reload of all host services'
    echo '  stopstart: gentle stop and start of all host services'
    echo '  reboot:  gentle stop of all host services and reboot the server'
    echo '  update:  runs apt-get update && upgrade'
    echo '  status:  status of all host services, their version and performs some basic hosts checks'
    echo '  clean:   free some disk space by deleting all logs and purging packages cache'
    echo '  collect: gathers some system info and archives them for later analysis'
    echo '  help:    help about this host (configuration, embedded commands...)'
}

# This message will be displayed if the script is called with -h or --help
help() {
    usage
    modulesCmd help
}

# The function below allows the checkXxxxx script to handle its own script options.
ACTION="status"
loadOptions() {
#    echo "(loadOptions) received options: $@"
    while [[ $1 ]]; do
        case "$1" in
            'stop'|'stopstart'|'start'|'restart'|'reboot'|'update'|'status'|'clean'|'collect'|'help')
                ACTION=$1
                # echo "test to run: $ACTION"
                shift 1
                ;;
            *)     #All remaining options will be treated by checkFunction
                options="${options} $1"
                shift 1
                ;;
        esac
    done
}

runAction() {
    case "${ACTION}" in
        "stop")
            syslogWarning "User just requested to stop all services"
            promptYesNo "stop all services" && stopAll
            ;;
        "start")
            startAll
            ;;
        "restart")
            syslogWarning "User just requested to restart all services"
            promptYesNo "restart all services" && restartAll
            ;;
        "stopstart")
            syslogWarning "User just requested to stop and start all services"
            promptYesNo "stop and start all services" && stopstartAll
            ;;
        "reboot")
            syslogWarning "User just requested a host reboot"
            if promptYesNo "stop all services and reboot the host"; then
                stopAll
                rebootHost
            fi
            ;;
        "status")
            statusAll
            ;;
        "help")
            help
            ;;
        "clean")
            clean
            ;;
        "collect")
            isVerbose=1
            BOOTUP=nocolor
            collectAll
            ;;
        "update")
            updateHostApt
            ;;
        *)
            echo
            echo "  /!\ Error: Unknown action: ${ACTION}"
            echo
            usage
            exit ${errorCallParameters}
            ;;
    esac
}

# Load the function file:
if [ ! -e /etc/hostctl/functions ]; then
    echo
    echo "  /!\ Internal Error. functions lib is missing"
    echo
    exit 104
fi
. /etc/hostctl/functions

if [ -e /etc/ansible.env ]; then
    . /etc/ansible.env
fi

# ---------------------------------------------------------
# Check Functions
# ---------------------------------------------------------

getServicePid() {
    systemctl show --property MainPID --value $1 2>/dev/null
}

getServiceUptime() {
    if [ -n "$2" ]; then
        [ -f "$2" ] && pid=$(cat "$2") || pid=0
    else
        pid=$(getServicePid $1)
    fi
    if [ $? != 0 ]; then
        echo '-'
        return 1
    fi
    serviceLastStartDate=$(date --date="$(ps -p $pid -o lstart=)" '+%s' 2>/dev/null)
    if [ $? != 0 ]; then
        echo '-'
        return 1
    fi
    seconds=$(( $(date +%s) - ${serviceLastStartDate} ))
    echo $(formatSeconds ${seconds})
}

getContainerUptime() {
    command="$*"
    ps -eo etime,pid,args|/bin/grep -v '/bin/grep'|/bin/grep "${command}">/tmp/container-info.txt
    while read line; do
        pid=$(echo ${line}|awk '{print $2}')
    done </tmp/container-info.txt
    if [ $? != 0 -o -z "$pid" ]; then
        echo '-'
        return 1
    fi
    serviceLastStartDate=$(date --date="$(ps -p $pid -o lstart=)" '+%s' 2>/dev/null)
    if [ $? != 0 ]; then
        echo '-'
        return 1
    fi
    seconds=$(( $(date +%s) - ${serviceLastStartDate} ))
    echo $(formatSeconds ${seconds})
}

checkPartition() {
    local partition=$1
    shift
    local partitionUse=$(df -P ${partition} 2>/dev/null | sed -n 2p | awk '{print $5}' | sed s/%//)
    if [ -z "${partitionUse}" ]; then
        displaySkipped "Partition ${partition} check error"
    elif [ "${partitionUse}" -gt  "${partionMaxSize}" ]; then
        logErrorWithDiagnosis "Partition ${partition}: ${partitionUse}% exceeds ${partionMaxSize}%" "$@"
    else
        displaySuccess "Partition ${partition}: ${partitionUse}%"
    fi
}

checkPartitionInodes() {
    local partition=$1
    shift
    local partitionUse=$(df -Pi ${partition} 2>/dev/null | sed -n 2p | awk '{print $5}' | sed s/%//)
    if [ -z "${partitionUse}" ]; then
        displaySkipped "Inodes in partition ${partition} check error"
    elif [ "${partitionUse}" == '-' ]; then
        displaySkipped "Inodes in partition ${partition} check error"
    elif [ "${partitionUse}" -gt  "${partionMaxSize}" ]; then
        logErrorWithDiagnosis "Inodes in partition ${partition}: ${partitionUse}% exceeds ${partionMaxSize}%" "$@"
    else
        displaySuccess "Inodes in partition ${partition}: ${partitionUse}%"
    fi
}

testPartitions() {
    #displayTitle "Disk size:"
    checkPartition "/" "use $(colored "clean" $colorCyan) command to free some space"
    checkPartitionInodes "/"
    logSize=`du -sh /var/log/|awk '{print $1}'`
    echo "  /var/log size:    ${logSize}"
}

testCpu () {
    # CPU load
    if [ ${isVerbose} == 1 ]; then
        echo
        displayTitle "CPU Load"
        top -b -n 1 | grep -v grep --max-count=12
    fi
}

secToTime() {
    local d=$1
    dSec=`expr ${d} % 60`
    dMin=`expr \( ${d} / 60 \) % 60`
    dHour=`expr ${d} / 3600`
    printf "%02d:%02d:%02d" "${dHour}" "${dMin}" "${dSec}"
}

timeDiff() {
    local t1=$1
    local t2=$2
    local d1=`date "+%s" -d "${t1}"`
    [ -z "${t2}" ] && local d2=`date "+%s"` || local d2=`date "+%s" -d "${t2}"`
    local dDiff=`expr ${d2} - ${d1}`
    [ ${dDiff} -lt 0 ] && dDiff=`expr ${d2} - ${d1} + 86400`
    secToTime ${dDiff}
}

# ---------------------------------------------------------
# Services management functions
# ---------------------------------------------------------

collectCommand(){
    echo "  running $2 ..."
    dest="/tmp/collectStatus/${2}.txt"
    echo -e "$(date "+%Y%m%d-%H%M%S") $1\n==============================\n\n" > ${dest}
    eval $1 >> ${dest} 2>&1
}

collectCopy(){
    echo "  copying $1 ..."
    dest="/tmp/collectStatus/$(basename ${1})"
    echo -e "$(date "+%Y%m%d-%H%M%S") $1\n==============================\n\n" > ${dest}
    cat $1 >> ${dest}
}

collectAll(){
    displaySection "Collect status"
    collectFolder=/tmp/collectStatus
    sudo rm -rf ${collectFolder}
    [ ! -z ${collectFolder} ] && mkdir -p ${collectFolder}
    collectCommand 'statusAll' 'status'
    collectCommand 'arp -a' 'arp'
    collectCommand 'free -mh' 'free'
    collectCommand 'df' 'df'
    collectCommand 'ip a' 'ips'
    collectCommand 'ip r' 'routes'
    collectCommand 'dpkg -l' 'dpkg'
    collectCommand 'top -bn 3' 'top'
    collectCommand 'ps -edf' 'ps'
    collectCommand 'lsof' 'lsof'
    collectCommand 'netstat -patun' 'netstat'
    collectCommand 'iptables -L -v' 'iptables'
    collectCommand 'dmesg -T' 'dmesg'
    collectCommand 'uptime' 'uptime'

    collectCopy "/var/log/kern.log"
    for s in /var/log/syslog*; do
        collectCopy "${s}"
    done

    modulesCmd collect

    archive=~/collect-${currentDate}
    password=$(cat /dev/urandom | tr -dc 'a-zA-Z0-9' | fold -w 32 | head -n 1)
    do_encrypt=1
    if [ ${do_encrypt} -eq 1 ]; then
        archive="${archive}.enc.tgz"
        $(tar -czf - ${collectFolder}/* | openssl enc -e -aes256 -k ${password} -out ${archive})
    else
        archive="${archive}.tgz"
        $(tar -czf ${archive} ${collectFolder})
    fi

    echo ""
    echo "###########################################"
    echo "#"
    echo "# File saved: ${archive} ($(folderSize ${archive} | humanPrint))"
    if [ ${do_encrypt} -eq 1 ]; then
        echo "# Archive has been encrypted with the following password: ${password}"
        echo "# Use the following to decrypt: openssl enc -d -aes256 -in ${archive} | tar xz -C DIR"
    fi
    echo "#"
    echo "###########################################"
    echo ""
}

statusAll(){
    displaySection "Host status"
    echo "Hostname: $(hostname -f) ($(hostname -I))"
    echo "Last reboot: $(uptime -p), on $(uptime -s)"
    if [ ! -z "$LAST_DEPLOY" ]; then
        echo -en "Last Ansible deployment has been performed on \e[1;34m${LAST_DEPLOY}\e[m $LAST_DEPLOY_TIME, "
        daysAgo=$(( ( $(date +'%s') - $(date -ud "$LAST_DEPLOY" +'%s') )/60/60/24 ))
        if [ "$daysAgo" == 0 ]; then
            echo -en today
        elif [ "$daysAgo" == 1 ]; then
            echo -en yesterday
        else
            echo -en "$daysAgo days ago"
        fi
        echo -en " by \e[1;34m${LAST_DEPLOY_USER}\e[m"
        echo
    fi
    if [ ! -z "$GIT_BRANCH" ]; then
        echo "Last Ansible deployment has been made from branch $GIT_BRANCH, commit $GIT_COMMIT"
    fi
    testPartitions
    testCpu

    modulesCmd status
}

# ---------------------------------------------------------
# Services management functions
# ---------------------------------------------------------

stopAll() {
    displaySection "Stopping all services"
    modulesCmd stop
}

startAll() {
    displaySection "Starting all services"
    modulesCmd start
}

restartAll() {
    displaySection "Restarting all services"
    modulesCmd restart
}

stopstartAll() {
    stopAll
    startAll
}

folderSize() {
    local resourcePath="$1"
    du -s "${resourcePath}" 2>/dev/null|awk '{print $1}'
}

humanPrint() {
    while read KB dummy; do
        # [ $B -lt 1024 ] && echo ${B} bytes && break
        # KB=$(((B+512)/1024))
        [ $KB -lt 1024 ] && echo ${KB}K && break
        MB=$(((KB+512)/1024))
        [ $MB -lt 1024 ] && echo ${MB}M && break
        GB=$(((MB+512)/1024))
        [ $GB -lt 1024 ] && echo ${GB}G && break
        echo $(((GB+512)/1024))T
    done
}

spaceSaved() {
    local before="$1"
    local after="$2"
    colored "$(echo $((before-after))|humanPrint)" $colorCyan
}

cleanLogs() {
    for logs in `find /var/log -name "*.[0-9]" -o -name "*.gz" 2>/dev/null`; do rm -fr $logs; done
    for logs in `find /var/log -type f -mtime +3 2>/dev/null`; do rm -fr $logs; done
    for logs in `find /var/log -type f 2>/dev/null`; do bash -c "echo '' > $logs"; done
}

cleanRsyslogCache() {
    rm -rf /var/spool/rsyslog/*
}

cleanApt() {
    apt-get clean -y -q
    apt-get autoremove -y -q
}

cleanExim4() {
    service exim4 stop
    rm -rf /var/spool/exim4/input /var/spool/exim4/msglog
    service exim4 start
}

cleanAction() {
    local messageBefore="$1"
    local resourcePath="$2"
    local action="$3"
    before=$(folderSize ${resourcePath})
    echo "${messageBefore}..."
    ${action}
    after=$(folderSize ${resourcePath})
    displaySuccess "Done. Space saved: $(spaceSaved ${before} ${after})"
    echo ""
}

clean() {
    echo ''
    echo $(underlined 'Clean filesystem')
    promptYesNo "safely $(underlined 'delete all logs')" && cleanAction "Clearing all logs" "/var/log" "cleanLogs"
    promptYesNo "clean $(underlined 'APT') cache and orphans" && cleanAction "Removing apt cache" "/var/cache/apt" "cleanApt"
    promptYesNo "clear $(underlined 'rsyslog') cache" && cleanAction "Removing rsyslog cache" "/var/spool/rsyslog" "cleanRsyslogCache"
    promptYesNo "remove exim4 (mailer) local messages" && cleanAction "Exim4 mails" "/var/spool/exim4" "cleanExim4"
}

updateHostApt() {
    apt-get update -y
    apt-get dist-upgrade -y
}

rebootHost() {
    echo
    echo "  /!\ Server will reboot in 2 seconds."
    echo
    nohup $(sleep 2 && shutdown -r 0) >/dev/null 2>&1 &
    exit 0
}

stopService() {
    local serviceName="$1"
    local killall="$2"
    local psGrep="$3"

    echo "Stopping ${serviceName}..."
    res=$(systemctl stop ${serviceName})
    if [ ! -z "${killall}" ]; then
        sleep 2
        echo "Killing ${serviceName}..."
        /usr/bin/killall ${serviceName}
    fi
    if [ ! -z "${psGrep}" ]; then
        # then we wait for the service to stop
        timer=0
        psRes=$(ps -edf|/bin/grep -v '/bin/grep'|/bin/grep "'"${psGrep}"'"|wc -l)
        until [ ${psRes} -eq 0 ] || [ ${timer} -eq ${stopServiceTimeout} ]; do
            progressBar
            ((timer++))
            sleep 1
            psRes=$(ps -edf|/bin/grep -v '/bin/grep'|/bin/grep  "'"${psGrep}"'"|wc -l)
        done
        progressBarStop
        if [ ${psRes} -eq 0 ]; then
            displaySuccess "Service $(underlined ${serviceName}) is stopped"
        else
            logErrorWithDiagnosis "Service $(underlined ${serviceName}) stop timed-out"
        fi
    fi
}

startService() {
    local serviceName="$1"
    shift 1
    local pingFunction=$@
    ${pingFunction}
    pingResult=$?
    if [ ${pingResult} -eq 0 ]; then
        displaySuccess "Service $(underlined ${serviceName}) is already started"
    else
        echo "Starting ${serviceName}..."
        systemctl start ${serviceName}
        exitCode=$?
        if [ "${exitCode}" -eq 0 ]; then
            ${pingFunction}
            pingResult=$?
            timer=0
            until [ ${pingResult} -eq 0 ] || [ ${timer} -eq ${startServiceTimeout} ]; do
                progressBar
                ((timer++))
                sleep 1
                ${pingFunction}
                pingResult=$?
            done
            progressBarStop
            if [ "${pingResult}" -eq 0 ]; then
                displaySuccess "Service $(underlined ${serviceName}) is started"
            else
                logErrorWithDiagnosis "Service $(underlined ${serviceName}) start timed-out"
            fi
        else
            logErrorWithDiagnosis "Service $(underlined ${serviceName}) start failed"
        fi
    fi
}

restartService() {
    local serviceName="$1"
    shift 1
    local pingFunction=$@
    echo "Restarting ${serviceName}..."
    systemctl restart ${serviceName}
    exitCode=$?
    if [ "${exitCode}" -eq 0 ]; then
        ${pingFunction}
        pingResult=$?
        timer=0
        until [ ${pingResult} -eq 0 ] || [ ${timer} -eq ${startServiceTimeout} ]; do
            progressBar
            ((timer++))
            sleep 1
            ${pingFunction}
            pingResult=$?
        done
        progressBarStop
        if [ "${pingResult}" -eq 0 ]; then
            displaySuccess "Service $(underlined ${serviceName}) is started"
        else
            logErrorWithDiagnosis "Service $(underlined ${serviceName}) start timed-out"
        fi
    fi
}

restartLoad() {
    local serviceName="$1"
    echo "Reloading ${serviceName}..."
    service ${serviceName} reload
    exitCode=$?
    if [ "${exitCode}" -eq 0 ]; then
        displaySuccess "Service $(underlined ${serviceName}) is reloaded"
    else
        logErrorWithDiagnosis "Service $(underlined ${serviceName}) reload failed"
    fi
}

stopContainer() {
    local containerName="$1"

    echo "Stopping ${containerName}..."
    res=$(docker stop ${containerName})
    if [ ${res} -eq 0 ]; then
        displaySuccess "Container $(underlined ${containerName}) is stopped"
    else
        logErrorWithDiagnosis "Container $(underlined ${containerName}) stop timed-out"
    fi
}

startContainer() {
    local containerName="$1"
    shift 1
    local pingFunction=$@
    ${pingFunction}
    pingResult=$?
    if [ ${pingResult} -eq 0 ]; then
        displaySuccess "Container $(underlined ${containerName}) is already started"
    else
        echo "Starting ${containerName}..."
        docker start ${containerName}
        exitCode=$?
        if [ "${exitCode}" -eq 0 ]; then
            ${pingFunction}
            pingResult=$?
            timer=0
            until [ ${pingResult} -eq 0 ] || [ ${timer} -eq ${startServiceTimeout} ]; do
                progressBar
                ((timer++))
                sleep 1
                ${pingFunction}
                pingResult=$?
            done
            progressBarStop
            if [ "${pingResult}" -eq 0 ]; then
                displaySuccess "Container $(underlined ${containerName}) is started"
            else
                logErrorWithDiagnosis "Container $(underlined ${containerName}) start timed-out"
            fi
        else
            logErrorWithDiagnosis "Container $(underlined ${containerName}) start failed"
        fi
    fi
}

restartContainer() {
    local containerName="$1"
    shift 1
    local pingFunction=$@
    echo "Restarting ${containerName}..."
    docker restart ${containerName}
    exitCode=$?
    if [ "${exitCode}" -eq 0 ]; then
        ${pingFunction}
        pingResult=$?
        timer=0
        until [ ${pingResult} -eq 0 ] || [ ${timer} -eq ${startServiceTimeout} ]; do
            progressBar
            ((timer++))
            sleep 1
            ${pingFunction}
            pingResult=$?
        done
        progressBarStop
        if [ "${pingResult}" -eq 0 ]; then
            displaySuccess "Container $(underlined ${containerName}) is started"
        else
            logErrorWithDiagnosis "Container $(underlined ${containerName}) start timed-out"
        fi
    fi
}

getServiceVersion() {
    if [ -z "$2" -o "$2" == 0 ]; then
        pkg=$(echo "$1" | cut -d '@' -f 1)
        res=$(dpkg -s $pkg 2>/dev/null)
        code=$?
        if [ ${code} -eq 0 ]; then
            if [ $isVerbose -eq 1 ]; then
                echo "${res}"|grep "^Version"|awk '{print $2}'
            else
                echo "${res}"|grep "^Version"|sed -r 's/^.*:\s*([^~\+]+).*$/\1/'
            fi
        else
            echo $(colored "missing" $colorRed)
        fi
    else
      echo "$2"
    fi
}

getServiceVersionShort() {
    pkg=$(echo "$1" | cut -d '@' -f 1)
    res=$(dpkg -s $pkg 2>/dev/null)
    code=$?
    if [ ${code} -eq 0 ]; then
        echo "${res}"|grep "^Version"|sed -r 's/^.*:\s*([^~\+]+).*$/\1/'
    else
        echo ""
    fi
}

checkService() {
    local serviceName=$1
    local packageName=$2
    local versionSet=$3
    local pidFile=$4
    [ -z "${packageName}" ] && packageName=${serviceName}
    [ -z "${versionSet}" ] && versionSet=0
    serviceFullName=$serviceName
    [[ $serviceName == *"."* ]] || serviceFullName=${serviceName}.service
    res=$(systemctl status ${serviceFullName} --no-legend --no-pager -l -n 0)
    exitCode=$?
    serviceVersion=$(getServiceVersion ${packageName} ${versionSet})
    serviceUptime=", up $(getServiceUptime ${serviceName} ${pidFile})"
    if [ "${exitCode}" -eq 0 ]; then
        displaySuccess "$(underlined ${serviceName}) ${serviceVersion}${serviceUptime}"
        return 0
    else
        logErrorWithDiagnosis "$(underlined ${serviceName}) ${serviceVersion} is not running"
        echo "$res" | head -n 3
        return 1
    fi
}

checkContainer() {
  local serviceName=${1}
  local serviceType="(c)"
  container=$(docker ps -a --no-trunc --filter Name="^${serviceName}\$" --format '{ "ID":"{{ .ID }}", "Name":"{{ .Names }}", "Status": "{{ .Status }}", "Image": "{{ .Image }}", "Command":{{ .Command }} }')
  if [ -z "${container}" ]; then
      logErrorWithDiagnosis "$(underlined ${serviceName}) ${serviceType} can't be found"
      return 1
  fi
  cjs=$(echo ${container} | python3 -m json.tool)
  image=$(echo ${cjs} | jq .Image)
  serviceVersion=$(echo $image | cut -d ':' -f 2 | cut -d '"' -f 1)
  command="$(echo ${cjs} | jq .Command | sed 's%\"\(.*\)\"%\1%' | sed 's%docker-entrypoint.sh \(.*\)%\1%')"
  serviceUptime=", up $(getContainerUptime ${command})"
  serviceStatus=$(echo ${cjs} | jq .Status)
  res=$(echo ${serviceStatus} | grep -q "Up")
  exitCode=$?
  if [ "${exitCode}" -eq 0 ]; then
      displaySuccess "$(underlined ${serviceName}) ${serviceVersion}${serviceUptime} ${serviceType}"
      return 0
  else
      logErrorWithDiagnosis "$(underlined ${serviceName}) ${serviceVersion} ${serviceType} is not running"
      echo "$res" | head -n 3
      return 1
  fi
}

pingUrl() {
    curl -sSifm1 $1 >/dev/null 2>&1
    return $?
}

pingService() {
    local serviceName="$1"
    service ${serviceName} status >/dev/null 2>&1
}

pingContainer() {
    local containerName="$1"
    pid=$(docker inspect ${containerName} | jq .[0].State.Pid)
    [ ${pid} -eq 0 ] && return 1 || return 0
}

processInfo() {
    [ ${isVerbose} = 0 ] && return 0;
    local processRegexp="$1"
    ps -eo etime,pid,args|/bin/grep -v '/bin/grep'|/bin/grep "${processRegexp}">/tmp/process-info.txt
    while read line; do
        etime=$(echo ${line}|awk '{print $1}')
        pid=$(echo ${line}|awk '{print $2}')
#        if [ ${isVerbose} = 1 ]; then
#            args=$(echo ${line}|awk '{$1 = $2 = ""; print $0;}'|sed -r 's/^ *//')
#        else
        args=$(echo ${line}|awk '{$1 = $2 = ""; print $0;}'|sed -r 's/^ *//'|cut -c1-50)
#        fi
        if [ ! -z "$(echo "${etime}"|grep '-')" ]; then
            elapsedTime=$(echo "${etime}"|sed -r 's/^([^-]+)-(.*)$/\1 days, \2/')
        else
            elapsedTime="${etime}"
        fi
        echo "  Process ${pid} uptime is $(colored """${elapsedTime}""" $colorCyan): ${args}"
    done </tmp/process-info.txt
}

check_broken_links() {
    in_folder=$1
    out=$(find ${in_folder} -type l ! -exec test -e {} \; -print)
    [ $? != 0 ] && logErrorWithDiagnosis "'${in_folder}' does not exist"
    if [ "${out}" == "" ]; then
        [ $isVerbose -eq 1 ] && displaySuccess "  ${in_folder} has no broken symlinks"
    else
        logErrorWithDiagnosis "'${in_folder}' has broken symlinks: ${out}"
    fi
}

# before starting the script you can uncommont following lines to change the script behaviour:
isDisplayOnly=1                  # activates the display mode, with no files storage on the host. values: 0, 1 ; default: 0
#isQuietMode=0                   # activates the quiet mode, with no output on console. values: 0, 1 ; default: 0
#isVerbose=0                     # activates the verbose mode, with more output in console like skipped tests. values: 0, 1 ; default: 0
#BOOTUP=color                    # choose if you want colors or not on console, with no files storage on the host. values: nocolor, color ; default: color

exitIfNotRoot                    # Exit the script if not launched as root
if [ "$(logname)" == "ro" ]; then
    case "$ACTION" in
        stop*|*start*|reboot|clean|collect|update)
            echo "Sorry $(logname), you're not allowed to run: $ACTION"
    	    exit 1
            ;;
		status|help|*)  # Access granted
            ;;
    esac
fi
startScript                # Execute this function to start your check script (load params, prepare logs, check script is not already running...)

# ---------------------------------------------------------
# Host analysis/description
# ---------------------------------------------------------

# load up all available module extensions
registerModules

# run the selected action
runAction

# Mandatory: end the functions.sh lib
endScript                     # Execute this function to end your your script (store archive, report errors...)
