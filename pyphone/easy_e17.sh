#!/usr/bin/env bash

#############################################################################
# This script is based on the very good prework from trickster.             #
# It is a result of the work from the people from #e.de (irc.freenode.net). #
# It will checkout the cvs and compile e17.                                 #
#                                                                           #
# License: BSD licence                                                      #
# Get the latest version at http://omicron.homeip.net/projects/#easy_e17.sh #
# Rewrite by morlenxus (morlenxus@gmx.net)                                  #
#                                                                           #
last_changes="2007-11-27"                                                   #
version="1.1.5"                                                             #
#############################################################################


# Edit these variables if you like:
install_path="/opt/e17"
cvs_path="$HOME/e17_cvs"
tmp_path="/tmp/easy_e17"
logs_path="$tmp_path/install_logs"
cvs_srv=":pserver:anonymous@anoncvs.enlightenment.org:/var/cvs/e";
conf_file="$HOME/.easy_e17.conf"

efl="imlib2 edb eet evas ecore efreet epeg embryo edje epsilon esmart emotion engrave etk etk_extra ewl exml enhance e_dbus"
apps="e entrance eclair evfs edje_viewer edje_editor elicit elitaire emphasis empower engycad entrance_edit_gui entropy ephoto estickies exhibit expedite exquisite extrackt e_phys"
apps_misc="enthrall rage scrot"
e17_modules="alarm bling calendar cpu deskshow emu flame forecasts language mail mem mixer moon net news penguins photo rain screenshot slideshow snow taskbar tclock uptime weather winselector wlan"

autogen_args=""		# evas:--enable-gl-x11
linux_distri=""		# if your distribution is wrongly detected, define it here
max_backoff=360		# Actual maximum backoff time is roughly this number in seconds.
nice_level=0		# nice level (19 == low, -20 == high)
os=$(uname)			# operating system
threads=2			# make -j <threads>

# URL of latest stable release
online_source="http://omicron.homeip.net/projects/easy_e17/easy_e17.sh"


#############################################################################
function logo ()
{
	clear
	echo -e "\033[1m-------------------------------\033[7m Easy_e17.sh $version \033[0m\033[1m------------------------------\033[0m"
	echo -e "\033[1m  Developers:\033[0m      Brian 'morlenxus' Miculcy"
	echo -e "                   David 'onefang' Seikel"
	echo -e "\033[1m  Contributors:\033[0m    Tim 'wtfoo' Zebulla"
	echo -e "                   Daniel G. '_ke' Siegel"
	echo -e "                   Stefan 'slax' Langner"
	echo -e "                   Massimiliano 'Massi' Calamelli"
	echo -e "                   Thomas 'thomasg' Gstaedtner"
	echo -e "\033[1m--------------------------------------------------------------------------------\033[0m"
	echo -e "\033[1m  Updates:\033[0m         http://omicron.homeip.net/projects/#easy_e17.sh"
	echo -e "\033[1m  Support:\033[0m         #e.de, #get-e (irc.freenode.net)"
	echo -e "                   morlenxus@gmx.net"
	echo -e "\033[1m  Patches:\033[0m         Generally accepted, please contact me!"
	echo -e "\033[1m--------------------------------------------------------------------------------\033[0m"
	echo 
	echo
	echo -e "\033[1m-----------------------------\033[7m Current Configuration \033[0m\033[1m----------------------------\033[0m"
	echo "  Install path:    $install_path"
	echo "  CVS path:        $cvs_path"
	echo "  CVS server:      $cvs_srv"
	echo "  Logs path:       $logs_path"
	if [ "$linux_distri" ]; then
		echo "  OS:              $os (Distribution: $linux_distri)"
	else
		echo "  OS:              $os"
	fi
	echo
	echo "  Libraries:       $efl"
	echo "  Applications:    $apps"
	echo "  Miscellaneous:   $apps_misc"
	echo "  Modules:         $e17_modules"
	if [ "$skip" ]; then
		echo "  Skipping:        $skip"
	fi
	if [ "$only" ]; then
		echo "  Only:            $only"
	fi
	echo
	if [ "$fullcvs" ]; then
		echo "  Full cvs:        yes"
	fi	
	if [ "$skip_cvsupdate" ]; then
		echo "  Skip cvs update: yes"
	fi
	if [[ clean -eq 1 ]] ; then
		echo "  Run clean:       yes"
	fi
	if [[ clean -eq 2 ]] ; then
		echo "  Run distclean:   yes"
	fi
	if [[ clean -ge 3 ]] ; then
		echo "  Run uninstall:   yes"
	fi
	if [ "$skip_errors" ]; then
		echo "  Skip errors:     yes"
	fi
	if [ "$gen_docs" ]; then
		echo "  Generate docs:   yes"
	fi
	if [ "$easy_e17_post_script" ]; then
		echo "  Post install:    $easy_e17_post_script"
	fi
	if [ "$autogen_args" ]; then
		echo "  Autogen args:    $autogen_args"
	fi
	if [ "$wait" ]; then
		echo "  Wait on exit:    yes"
	fi		
	if [ "$keep" ]; then
		echo "  Keep tempdir:    yes"
	fi
	if [ "$accache" ]; then
		echo "  Use caches:      yes"
	fi
	if [ "$threads" -ne 2 ]; then
		echo "  Threads:         $threads"
	fi
	if [ "$nice_level" -ne 0 ]; then
		echo "  Nice level:      $nice_level"
	fi	
	if [ -z "$action" ]; then
		action="MISSING!"
	fi
	echo "  Script action:   $action"
	echo -e "\033[1m--------------------------------------------------------------------------------\033[0m"
	echo
	
	if [ "$action" == "script" ]; then
		return
	fi	

	if [ $1 == 0 ]; then
		if [ "$2" ]; then
			echo -e "\033[1m-------------------------------\033[7m Bad script argument \033[0m\033[1m----------------------------\033[0m"
			echo -e "  \033[1m$2\033[0m"
		fi
	else
		echo -e "\033[1m--------------------------------\033[7m Build phase $1/3 \033[0m\033[1m-------------------------------\033[0m"
	fi

	if [ -z "$2" ]; then
		case $1 in
			0)
				if [ "$os" == "not supported" ]; then
					echo -e "\033[1m-------------------------------\033[7m Not supported OS \033[0m\033[1m------------------------------\033[0m"
				  	echo "  Your operating system '$(uname)' is not supported by this script."
					echo "  If possible please provide a patch."
				else if [ -z "$fullhelp" ]; then
					echo -e "\033[1m-----------------\033[7m Short help 'easy_e17.sh <ACTION> <OPTIONS...>' \033[0m\033[1m---------------\033[0m"
					echo "  -i, --install    = action: compile and install ALL of e17"
					echo "  -u, --update     = action: update your installed e17"
					echo "      --help       = full help"
				else
					echo -e "\033[1m-----------------\033[7m Full help 'easy_e17.sh <ACTION> <OPTIONS...>' \033[0m\033[1m----------------\033[0m"
					echo -e "  \033[1mACTION (ONLY ONE SELECTION POSSIBLE):\033[0m"
					echo "  -i, --install                       = action: compile and install ALL of e17"
					echo "  -u, --update                        = action: update your installed e17"
					echo "  -c, --clean                         = action: clean the sources"
					echo "                                        (more --cleans means more cleaning, up"
					echo "                                        to a maximum of three, which will"
					echo "                                        uninstall e17."
					echo "                                        If used with one of the other actions,"
					echo "                                        this will clean first.)"
					echo "      --only=<name1>,<name2>,...      = action: checkout and compile ONLY the"
					echo "                                        named libs/apps"
					echo "      --cvsupdate                     = update only the cvs tree"
					echo "  -v, --check-script-version          = check for a newer release of easy_e17"
					echo "      --help                          = this help"
					echo
					echo -e "  \033[1mOPTIONS:\033[0m"
					echo "      --conf=<file>                   = use an alternate configuration file"
					echo "      --instpath=<path>               = change the default install path"
					echo "      --cvspath=<path>                = change the default cvs path"
					echo "      --cvssrv=<server>               = change the default cvs server"
					echo "      --asuser                        = do everything as the user, not as root"
					echo "      --fullcvs                       = checkout optional cvs repositories:"
					echo "                                        - devs"
					echo "                                        - web"
					echo "  -s, --skip-cvsupdate                = no update for your local cvs copy"
					echo "  -f, --fix-cvs-conflicts             = deletes conflicting cvs files"
					echo "      --skip=<name1>,<name2>,...      = this will skip installing the named"
					echo "                                        libs/apps"
					echo "  -d, --docs                          = generate programmers documentation"
					echo "      --postscript=<name>             = full path to a script to run as root"
					echo "                                        after installation"
					echo "  -e, --skip-errors                   = continue compiling even if there is"
					echo "                                        an error"
					echo "  -w, --wait                          = don't exit the script after finishing,"
					echo "                                        this allows 'xterm -e ./easy_e17.sh -i'"
					echo "                                        without closing the xterm"
					echo "  -k, --keep                          = don't delete the temporary dir"
					echo
					echo "  -l, --low                           = use lowest nice level (19, slowest,"
					echo "                                        takes more time to compile, select"
					echo "                                        this if you need to work on the pc"
					echo "                                        while compiling)"
					echo "      --normal                        = default nice level ($nice_level),"
					echo "                                        will be automatically used"
					echo "  -h, --high                          = use highest nice level (-20, fastest,"
					echo "                                        slows down the pc)"
					echo "      --cache                         = Use a common configure cache and"
					echo "                                        ccache if available"
					echo "      --threads=<int>                 = make can use threads, recommended on smp"
					echo "                                        systems (default: 2 threads)"
					echo
					echo "      --efl=<name1>,<name2>,...       = compile libraries in this order"
					echo "      --apps=<name1>,...              = compile e17 applications in this order"
					echo "      --apps_misc=<name1>,...         = compile e17 misc in this order"
					echo "      --e17_modules=<name1>,...       = compile e17 modules in this order"
					echo "      --autogen_args=<n1>:<o1>+<o2>,. = pass some options to autogen:"
					echo "                                        <name1>:<opt1>+<opt2>,<name2>:<opt1>+..."
					echo "      --cflags=<flag1>,<flag2>,...    = pass cflags to the gcc"
					echo -e "\033[1m--------------------------------------------------------------------------------\033[0m"
					echo
					echo -e "\033[1m----------------------\033[7m Configurationfile '~/.easy_e17.conf' \033[0m\033[1m--------------------\033[0m"
					echo "  Just create this file and save your favourite arguments."
					echo "  Example: If you use a diffent cvs path, add this line:"
					echo "           --cvspath=/home/brian.miculcy/enlightenment/e17_cvs"
				fi fi
				;;
			1)
				echo "- running some basic system checks"
				echo "- pre cleaning"
				echo "- cvs checkout/update"
				;;
			2)
				echo "- lib-compilation and installation"
				echo "- apps-compilation and installation"
				;;
			3)
				echo "- cleaning"
				echo "- install notes"
				;;
		esac
	fi
	echo -e "\033[1m--------------------------------------------------------------------------------\033[0m"
	echo
	echo
}

function define_os_vars ()
{
	case $os in
		SunOS)
			ldconfig="$(which crle) -u"	# there is no command like ldconfig on solaris! "crle" does nearly the same.
			make="make"
			export CFLAGS="$CFLAGS"
		;;
		Linux)
			ldconfig="/sbin/ldconfig"
			make="make"
			export CFLAGS="$CFLAGS"

			if [ -z "$linux_distri" ]; then
				if [ -e "/etc/debian_version" ];	then linux_distri="debian";	fi
				if [ -e "/etc/gentoo-release" ];	then linux_distri="gentoo";	fi
				if [ -e "/etc/redhat-release" ];	then linux_distri="redhat";	fi
				if [ -e "/etc/SuSE-release" ];		then linux_distri="suse";	fi
			fi
		;;
		FreeBSD)
			ldconfig="/sbin/ldconfig"
			make="gmake"
			export PATH=/usr/local/gnu-autotools/bin:$PATH
			export ACLOCAL_FLAGS=" -I /usr/local/share/aclocal"
			export CFLAGS="$CFLAGS -lintl -liconv -L/usr/local/lib -L/usr/X11R6/lib -I/usr/local/include -I/usr/X11R6/include"
			export CPPFLAGS="$CPPFLAGS -I/usr/local/include"
		;;
		*)
			os="not supported"
			logo 0
			exit
			;;
	esac
}

function find_path ()
{
	basedir="$cvs_path/$1"
	name=$2
	path=""
	for dir in `find "$basedir" -type d -name "$name" | awk -F "$cvs_path/" '{print $2}' | egrep -v -i "/bin/|/cvs/|/data/|/docs/|/oe/|/src/|/test/"`; do
		if [ "${#dir}" -lt "${#path}" ] || [ -z "$path" ]; then
			path=$dir
		fi
	done
	echo "$cvs_path/$path"
}

function backoff_loop
{
	cvscommand=$1

	backoff=$(( 4 + (RANDOM % 5) ))
	attempt=1;

	while [ 1 ]; do
		$cvscommand | tee -a "$tmp_path/cvs_update.log"
		if [ "${PIPESTATUS[0]}" -gt 0 ]; then
			if [ "$fix_cvs_conflicts" ]; then
				for cfile in `egrep "^[C] " "$tmp_path/cvs_update.log" | cut -d' ' -f2`; do
					echo "- fixing cvs conflict: $cfile"
					if [ -e "$cfile" ]; then
						rm "$cfile"
					fi
				done
			fi

			attempt=$(($attempt + 1))
			for (( i = $backoff / 2; i > 0; i-- )) do
    	        set_title "Checkout FAILED! Next attempt $attempt in $i seconds"
				echo -n -e "\rFAILED! Next attempt $attempt in \033[1m$i\033[0m seconds"
				sleep 1
			done
			echo -n -e "\r                                                            \r"
			if [[ backoff -le max_backoff ]] ; then
				backoff=$(( ($backoff * 2) + (RANDOM % 5) ))
			fi
		else
			break
		fi
	done
}

function get_cvs ()
{
	repo=$1

	cd $cvs_path
	if [ -d "$repo" ]; then
        if [ -n "$only" ]; then
            set_title "Updating source of '$repo' ($pkg_pos/$pkg_total)"
			echo "- updating source of '`basename "$repo"`' (please wait, this won't output much) ..."
        else
            set_title "Updating source of repo '$repo'"
			echo "- updating source of repo '$repo' (please wait, this won't output much) ..."
        fi
		cd "$repo"
		backoff_loop "cvs -z3 -q update -dP" 
	else
        if [ -n "$only" ]; then
            set_title "Checkout source of '$repo' ($pkg_pos/$pkg_total)"
			echo "- checkout source of '`basename "$repo"`' ..."
        else
            set_title "Checkout source of repo '$repo'"
			echo "- checkout source of repo '$repo' ..."
        fi
		backoff_loop "cvs -z3 -q -d $cvs_srv co $repo"
	fi
	echo
}

function build_each ()
{
	repo="$1"
	array=$2
	
	for name in $array
	do
		path=`find_path $repo $name`
		compile "$name" "$path"
	done
}

function run_command ()
{
	name=$1
	path=$2
	title=$3
	log_title=$4
	mode_needed=$5
	cmd=$6

	set_title "$name: $title ($pkg_pos/$pkg_total)"
	echo -n "$log_title"
	logfile_banner "$cmd" "$logs_path/$name.log"

	if [ $mode_needed == "rootonly" ]; then
		mode_needed=$mode
	else
		if [ $nice_level -ge 0 ]; then
			mode_needed="user"
		fi
	fi
	rm -f $tmp_path/$name.noerrors
	case "$mode_needed" in
		"sudo")
			echo "$sudopwd" | sudo -S nice -n $nice_level $cmd >> "$logs_path/$name.log" 2>&1 && touch $tmp_path/$name.noerrors &
			;;
		*)
			nice -n $nice_level $cmd >> "$logs_path/$name.log" 2>&1 && touch $tmp_path/$name.noerrors &
			;;
	esac	

	pid="$!"
	rotate "$pid" "$name"
}

function compile ()
{
	name=$1
	path=$2
	cnt=${#name}
	max=27
	make_extra=""

	touch "$logs_path/$name.log"
	rm $tmp_path/$name.noerrors 2>/dev/null
	echo -n "- $name "
	while [ ! $cnt = $max ]
	do
		echo -n "."
		cnt=`expr $cnt + 1`
	done
	echo -n " "

	for one in $skip
	do
		if [ "$name" == "$one" ]; then
			echo "SKIPPED"
			touch $tmp_path/$name.skipped
			return
		fi
	done
	if [ "$only" ] || [ "$action" == "update" ]; then
		found=""
		for one in $only
		do
			if [ "$name" == "$one" ]; then
				found=1
			fi
		done
		if [ -z "$found" ]; then
			echo "SKIPPED"
			touch $tmp_path/$name.skipped
			return
		fi
	fi

	if [ ! -d "$path" ]; then
		echo "NOT FOUND"
		return
	fi
	cd "$path"

	touch "$logs_path/$name.log"
	pkg_pos=`expr $pkg_pos + 1`

	if [[ clean -ge 1 ]] ; then
		rm -f "$logs_path/$name.log"
		touch "$logs_path/$name.log"
		if [ ! -e "Makefile" ]; then
		    echo "can't clean"
		    return
		fi
		if [[ clean -eq 1 ]] ; then
			cmd="$make clean"
			logfile_banner "$cmd" "$logs_path/$name.log"
		    $cmd >> "$logs_path/$name.log" 2>&1 && touch $tmp_path/$name.noerrors &
		fi
		if [[ clean -eq 2 ]] ; then
		    echo -n "distclean:  "
			cmd="$make clean distclean"
			logfile_banner "$cmd" "$logs_path/$name.log"
		    $cmd >> "$logs_path/$name.log" 2>&1 && touch $tmp_path/$name.noerrors &
		fi
		if [[ clean -ge 3 ]] ; then
		    echo -n "uninstall:  "
			cmd="$make uninstall clean distclean"
			logfile_banner "$cmd" "$logs_path/$name.log"
		    case "$mode" in
			"sudo")
			    echo "$sudopwd" | sudo -S nice -n $nice_level $cmd >> "$logs_path/$name.log" 2>&1 && touch $tmp_path/$name.noerrors &
			    ;;
			*)
			    nice -n $nice_level $cmd >> "$logs_path/$name.log" 2>&1 && touch $tmp_path/$name.noerrors &
			    ;;
		    esac
		    # It's no longer installed if we just uninstalled it.
		    # Even if the uninstall failed, it's best to mark it as uninstalled so that a partial uninstall gets fixed later.
		    rm -f $tmp_path/$name.installed
		fi
		pid="$!"
		rotate "$pid" "$name"
		rm -f $tmp_path/$name.noerrors
		echo "ok"
		return
	fi

	if [ -e "$tmp_path/$name.installed" ]; then
		echo "previously installed"
		return
	fi

	# get autogen arguments
	args=""
	for app_arg in `echo $autogen_args | tr -s '\,' ' '`
	do
		app=`echo $app_arg | cut -d':' -f1`
		if [ "$app" == "$name" ]; then
			args="$args `echo $app_arg | cut -d':' -f2- | tr -s '+' ' '`"
		fi
	done
	
	if [ -e "autogen.sh" ]; then
		run_command "$name" "$path" "autogen" "autogen:    " "$mode" "./autogen.sh --prefix=$install_path $accache $args"
		if [ ! -e "$tmp_path/$name.noerrors" ] ; then return ; fi
	else
		if [ -e "bootstrap" ]; then
			run_command "$name" "$path" "bootstrap" "bootstrap:  " "$mode" "./bootstrap"
			if [ ! -e "$tmp_path/$name.noerrors" ] ; then return ; fi
			run_command "$name" "$path" "configure" "configure:  " "$mode" "./configure --prefix=$install_path $accache $args"
			if [ ! -e "$tmp_path/$name.noerrors" ] ; then return ; fi
		else
			if [ -e "Makefile.PL" ]; then
				run_command "$name" "$path" "perl" "perl make:  " "$mode" "perl Makefile.PL prefix=$install_path $args"
				if [ ! -e "$tmp_path/$name.noerrors" ] ; then return ; fi
			else
				if [ -e "Makefile" ]; then
					make_extra="PREFIX=$install_path"
				else
					echo "no build system"
					touch $tmp_path/$name.nobuild
					return
				fi
			fi
		fi
	fi
	
	run_command "$name" "$path" "make" "make   :    " "$mode" "$make $make_extra -j $threads"
	if [ ! -e "$tmp_path/$name.noerrors" ] ; then return ; fi

	if [ "$gen_docs" ]; then
		if [ -e "gendoc" ]; then
			run_command "$name" "$path" "docs" "docs   :    " "$mode" "sh gendoc"
			if [ ! -e "$tmp_path/$name.noerrors" ] ; then return ; fi
		fi
	fi

	run_command "$name" "$path" "install" "install:    " "rootonly" "$make $make_extra install"
	if [ ! -e "$tmp_path/$name.noerrors" ] ; then return ; fi

	# All done, mark it as installed OK.
	touch $tmp_path/$name.installed
	rm -f $tmp_path/$name.noerrors
	echo "ok"
}

function rotate ()
{
	pid=$1
	name=$2
	star=1
	log_line=""
	
	while [ "`ps -p $pid -o comm=`" ]
	do
		last_line=`tail -1 "$logs_path/$name.log"`
		if [ ! "$log_line" = "$last_line" ]; then
			echo -e -n "\b\b\b"
			case $star in
				1)
					echo -n "["
					echo -n -e "\033[1m|\033[0m"
					echo -n "]"
					star=2
				;;
				2)
					echo -n "["
					echo -n -e "\033[1m/\033[0m"
					echo -n "]"
					star=3
				;;
				3)
					echo -n "["
					echo -n -e "\033[1m-\033[0m"
					echo -n "]"
					star=4
				;;
				4)
					echo -n "["
					echo -n -e "\033[1m"
					echo -n "\\"
					echo -n -e "\033[0m"
					echo -n "]"
					star=1
				;;
			esac
			log_line=$last_line
		fi
		sleep 1
	done

	del_lines 12
	if [ ! -e "$tmp_path/$name.noerrors" ]; then
		echo -e "\033[1mERROR!\033[0m"

		if [ ! "$skip_errors" ]; then
        	set_title "$name: ERROR"
			echo -e "\033[1m--------------------------------------------------------------------------------\033[0m"
			echo
			echo -e "\033[1m-----------------------------------\033[7m Last loglines \033[0m\033[1m------------------------------\033[0m"
			echo -n -e "\033[1m"
			tail -25 "$logs_path/$name.log"
			echo -n -e "\033[0m"
			echo -e "\033[1m--------------------------------------------------------------------------------\033[0m"
			echo
			echo "-> Get more informations by checking the log file '$logs_path/$name.log'!"
			echo
			exit
		fi
	fi
}

function del_lines ()
{
	cnt=0
	max=$1
	while [ ! "$cnt" == "$max" ]
	do
		echo -n -e "\b \b"
		cnt=`expr $cnt + 1`
	done
}

function error ()
{
    set_title "ERROR: $1"
	echo -e "\n\n\033[1mERROR: $1\033[0m\n\n"
	exit 2
}

function set_title ()
{
	if [ "$1" ]; then
		message="- $1"
	fi	

	if [ "$DISPLAY" ]; then
	    case "$TERM" in
			xterm*|rxvt*|Eterm|eterm|Aterm|aterm)
	        	echo -ne "\033]0;Easy_e17.sh $message\007"
				;;
	    esac
	fi	
}

function logfile_banner ()
{
	cmd=$1
	logfile=$2
	echo "-------------------------------------------------------------------------------" >> "$logfile"
	echo "EASY_E17 CMD: $cmd"						>> "$logfile"
	echo "-------------------------------------------------------------------------------" >> "$logfile"
}

function get_repo ()
{
    if [ -n "$only" ]; then
		# single install
        for pkg in $only
        do
            for each in $efl
            do
                if [ "$each" == "$pkg" ]; then
					path=`find_path "e17/" "$pkg"`
                    get_cvs "$path"
                fi
            done

            for each in $apps
            do
                if [ "$each" == "$pkg" ]; then
					path=`find_path "e17/" "$pkg"`
                    get_cvs "$path"
                fi
            done

            for each in $apps_misc
            do
                if [ "$each" == "$pkg" ]; then
					path=`find_path "misc/" "$pkg"`
                    get_cvs "$path"
                fi
            done

            for each in $e17_modules
            do
                if [ "$each" == "$pkg" ]; then
					path=`find_path "e_modules/" "$pkg"`
                    get_cvs "$path"
                fi
            done
        done
    else
    	# full install    
        get_cvs e17
        get_cvs misc
        get_cvs e_modules
		if [ "$fullcvs" ]; then
	        get_cvs devs
			get_cvs web
		fi
    fi
}

function cnt_pkgs () {
    pkg_total=0
    pkg_pos=0
    
    if [ -n "$only" ]; then
        for each in $only
        do
            pkg_total=`expr $pkg_total + 1`
        done  
    else
        # Maybe some regexp which counts the spaces is faster?
        total_pkgs="$efl $apps $apps_misc $e17_modules"
        for each in $total_pkgs
        do
            pkg_total=`expr $pkg_total + 1`
        done
    fi
} 

function check_script_version ()
{
	echo "- local version .............. $version"
	echo -n "- downloading script ......... " 
	remote_version=`wget $online_source  -q -U "easy_e17.sh/$version" -O - | grep -m 2 -o [0-9]\.[0-9]\.[0-9] | sort -n | head -n 1`
	echo "ok"
	echo "- remote version ............. $remote_version"	
	remote_ver=`echo "$remote_version" | tr -d '.'`
	local_ver=`echo "$version" | tr -d '.'`
	echo
	echo -n "- update available ........... "
	if [ $remote_ver -gt $local_ver ]; then
		echo -e "\033[1mYES!\033[0m"
	else
		echo "no"
	fi 
}


# SCRIPT: 

EASY_PWD=`pwd`
set_title 
define_os_vars
accache=""
easy_options=""
command_options=$@
clean=0

# Check for alternate conf file first.
test_options=$command_options
for arg in $test_options
do
	option=`echo "'$arg'" | cut -d'=' -f1 | tr -d "'"`
	value=`echo "'$arg'" | cut -d'=' -f2- | tr -d "'"`
	if [ "$value" == "$option" ]; then
		value=""
	fi
	if [ "$option" == "--conf" ]; then
		conf_file=$value;
	fi 
done

if [ -e "$conf_file" ]; then
	# load configfile 
	for option in `cat "$conf_file"`
	do
		easy_options="$easy_options $option"
	done
fi

# append arguments
easy_options="$easy_options $command_options" 

# check options
for arg in $easy_options
do
	option=`echo "'$arg'" | cut -d'=' -f1 | tr -d "'"`
	value=`echo "'$arg'" | cut -d'=' -f2- | tr -d "'"`
	if [ "$value" == "$option" ]; then
		value=""
	fi

	# $action can't be set twice
	if [ "$action" ]; then 
		if [ "$option" == "-i" ] ||
		   [ "$option" == "--install" ] ||
		   [ "$option" == "-u" ] ||
		   [ "$option" == "--update" ] ||
		   [ "$option" == "--only" ] ||
		   [ "$option" == "--cvsupdate" ] ||
		   [ "$option" == "-v" ] ||
		   [ "$option" == "--check-script-version" ]; then
			logo 0 "Only one action allowed! (currently using '--$action' and '$option')"
			exit
		fi
	fi
	
	case "$option" in
		"-i")						action="install" ;;
		"--install")				action="install" ;;
		"-u")						action="update" ;;
		"--update")					action="update" ;;
		"-c")						clean=$(( $clean + 1 ))	;;
		"--clean")					clean=$(( $clean + 1 ))	;;
		"--conf")					;;
		"--only")
			if [ -z "$value" ]; then
				logo 0 "Missing value for argument '$option'!"
				exit
			fi
			action="only"
			only="`echo "$value" | tr -s '\,' '\ '` $only"
			;;
		"-v")						action="script" ;;
		"--check-script-version")	action="script" ;;
		"--cvsupdate")
			action="cvsupdate"
			skip="$efl $apps $apps_misc $e17_modules"
			;;
		"--instpath")				install_path="$value" ;;
		"--cvspath")				cvs_path="$value" ;;
		"--cvssrv")
			cvs_srv="$value"
			export CVS_RSH="ssh"
			;;
		"--asuser")					asuser=1 ;;
		"-d")						gen_docs=1 ;;
		"--docs")					gen_docs=1 ;;
		"--postscript")				easy_e17_post_script="$value" ;;
		"--fullcvs")				fullcvs=1 ;;
		"-s")						skip_cvsupdate=1 ;;
		"--skip-cvsupdate")			skip_cvsupdate=1 ;;
		"-f")						fix_cvs_conflicts=1 ;;
		"--fix-cvs-conflicts")		fix_cvs_conflicts=1 ;;
		"--skip")
			if [ -z "$value" ]; then
				logo 0 "Missing value for argument '$option'!"
				exit
			fi
			skip="`echo "$value" | tr -s '\,' '\ '` $skip"
			;;
		"-e")						skip_errors=1 ;;
		"--skip-errors")			skip_errors=1 ;;		
		"-w")						wait=1 ;;
		"--wait")					wait=1 ;;
		"-k")						keep=1 ;;
		"--keep")					keep=1 ;;

		"-l")	 					nice_level=19 ;;
		"--low") 					nice_level=19 ;;
		"--normal") ;;
		"-h")	 					nice_level=-20 ;;
		"--high") 					nice_level=-20 ;;
		"--cache")
			accache=" --cache-file=$tmp_path/easy_e17.cache"
			ccache=`whereis ccache`
			if [ ! "$ccache" = "ccache:" ]; then
			    export CC="ccache gcc"
			fi
			;;
		"--threads")
			if [ -z "$value" ] || ! expr "$value" : "[0-9]*$" >/dev/null || [ "$value" -lt 1 ]; then
				logo 0 "Missing value for argument '$option'!"
				exit
			fi
			threads=$value
			;;

		"--efl")
			if [ -z "$value" ]; then
				logo 0 "Missing value for argument '$option'!"
				exit
			fi
			efl="`echo "$value" | tr -s '\,' '\ '`"
			;;
		"--apps")
			if [ -z "$value" ]; then
				logo 0 "Missing value for argument '$option'!"
				exit
			fi
			apps="`echo "$value" | tr -s '\,' '\ '`"
			;;
		"--apps_misc")
			if [ -z "$value" ]; then
				logo 0 "Missing value for argument '$option'!"
				exit
			fi
			apps_misc="`echo "$value" | tr -s '\,' '\ '`"
			;;
		"--e17_modules")
			if [ -z "$value" ]; then
				logo 0 "Missing value for argument '$option'!"
				exit
			fi
			e17_modules="`echo "$value" | tr -s '\,' '\ '`"
			;;
		"--autogen_args")	
			if [ -z "$value" ]; then
				logo 0 "Missing value for argument '$option'!"
				exit
			fi
			autogen_args="$value"
			;;
		"--cflags")
			if [ -z "$value" ]; then
				logo 0 "Missing value for argument '$option'!"
				exit
			fi
			CFLAGS="$CFLAGS `echo "$value" | tr -s '\,' '\ '`"
			;;
		"--help")
			fullhelp=1
			logo 0
			exit
			;;
		*)
			logo 0 "Unknown argument '$option'!"
			exit
			;;
	esac
done


# Sanity check stuff if doing everything as user.
if [ "$asuser" ]; then
    if [ $nice_level -lt 0 ]; then
	nice_level=0
    fi
fi

# special case to allow uninstall
if [ -z "$action" ] && [ "$clean" -ge 1 ]; then
	action="clean"
fi

# quit if some basic option is missing
if [ -z "$action" ] || [ -z "$install_path" ] || [ -z "$cvs_path" ]; then
	logo 0
	exit
fi

# check for script updates
if [ "$action" == "script" ]; then
	logo 0
	echo -e "\033[1m------------------------------\033[7m Check script version \033[0m\033[1m----------------------------\033[0m"
	check_script_version
	echo -e "\033[1m--------------------------------------------------------------------------------\033[0m"
	echo
	exit 0
fi


# run script normally
logo 1
set_title "Basic system checks"
echo -e "\033[1m-------------------------------\033[7m Basic system checks \033[0m\033[1m----------------------------\033[0m"
echo -n "- cvs-dir .................... " 
mkdir -p "$cvs_path" 2>/dev/null
if [ ! -w "$cvs_path" ]; then
	error "The cvs-dir '$cvs_path' isn't writeable!"
else
	echo "ok"
fi
touch "$HOME/.cvspass" 2>/dev/null

echo -n "- creating script dirs ....... "
mkdir -p "$tmp_path" 2>/dev/null
chmod 700 "$tmp_path"
mkdir -p "$logs_path" 2>/dev/null
echo "ok"

if [ ! "$action"  == "cvsupdate" ]; then
	echo -n "- build-user ................. "
	if [ ! "$LOGNAME" == "root" ]; then
		if [ "$asuser" ]; then
			echo "$LOGNAME (as user)"
			mode="user"
		else
			echo "$LOGNAME (non-root)"
			echo -n "- sudo available ............. "
			sudotest=`type sudo &>/dev/null ; echo $?`
			if [ "$sudotest" == 0 ]; then
				sudo -K
				if [ -e "$tmp_path/sudo.test" ]; then
					rm -f "$tmp_path/sudo.test"
				fi
				while [ -z "$sudopwd" ]
				do
					echo -n "enter sudo-password: "
					stty -echo
					read sudopwd
					stty echo
		
					# password check
					echo "$sudopwd" | sudo -S touch "$tmp_path/sudo.test" &>/dev/null
					if [ ! -e "$tmp_path/sudo.test" ]; then
						sudopwd=""
					fi
				done
				echo 
				mode="sudo"
				rm -f "$tmp_path/sudo.test"
			    else
				error "You're not root and sudo isn't available. Please run this script as root!"
			fi
		fi
	else
		echo "root"
		mode="root"
	fi

	echo -n "- adding path to env ......... " 
	export PATH="$install_path/bin:$PATH"
	export PKG_CONFIG_PATH="$install_path/lib/pkgconfig:$PKG_CONFIG_PATH"
	export LD_LIBRARY_PATH="$install_path/lib:$LD_LIBRARY_PATH"
	echo "ok"
	
	echo -n "- checking lib-path in ldc ... "
	case $os in
		FreeBSD) ;; # placeholder
		SunOS)	 ;; # need more testing of adding libraries on different solaris versions. atm this is not working
		Linux)
			libpath="`grep -r -l -i -m 1 $install_path/lib /etc/ld.so.conf*`"
			if [ -z "$libpath" ]; then
				case $linux_distri in
					gentoo)
						e17ldcfg="/etc/env.d/40e17paths"
						echo -e "PATH=$install_path/bin\nROOTPATH=$install_path/sbin:$install_path/bin\nLDPATH=$install_path/lib\nPKG_CONFIG_PATH=$install_path/lib/pkgconfig" > $e17ldcfg 
						env-update &> /dev/null
						echo "ok (path has been added to $e17ldcfg)";
						;;

					*)
						if [ "`grep -l 'include /etc/ld.so.conf.d/' /etc/ld.so.conf`" ]; then
							e17ldcfg="/etc/ld.so.conf.d/e17.conf"
							rm $e17ldcfg 2>/dev/null
						else
							e17ldcfg="/etc/ld.so.conf";
							cp $e17ldcfg $tmp_path;
						fi

						case "$mode" in
							"user") ;;
							"root")	echo "$install_path/lib" >>$e17ldcfg ;;
							"sudo")
								echo "$install_path/lib" >> $tmp_path/`basename $e17ldcfg`
								echo "$sudopwd" | sudo -S mv -f $tmp_path/`basename $e17ldcfg` $e17ldcfg
								;;
						esac
						if [ "$asuser" ]; then
							echo "skipped (running as user)";
						else
							echo "ok (path has been added to $e17ldcfg)";
						fi
						;;
				esac
			else
				echo "ok ($libpath)";
			fi
			;;
	esac

	echo -n "- setting compile options .... "
	export CPPFLAGS="$CPPFLAGS -I$install_path/include"
	export LDFLAGS="$LDFLAGS -L$install_path/lib"
	echo "ok"
fi

echo -e "\033[1m--------------------------------------------------------------------------------\033[0m"
echo


# do the clean first if not just cleaning.
if [[ clean -ge 1 ]] ; then
    if [ "$action" != "clean" ]; then
	set_title "Pre cleaning"
	sleep 5

	echo -e "\033[1m----------------------------\033[7m Precleaning libraries (EFL) \033[0m\033[1m-----------------------\033[0m"
	pkg_pos=0
	build_each "e17/" "$efl"
	echo -e "\033[1m--------------------------------------------------------------------------------\033[0m"
	echo

	echo -e "\033[1m-----------------------------\033[7m Precleaning applications \033[0m\033[1m-------------------------\033[0m"
	build_each "e17/" "$apps"
	build_each "misc/" "$apps_misc"
	echo -e "\033[1m--------------------------------------------------------------------------------\033[0m"
	echo

	echo -e "\033[1m-----------------------------\033[7m Precleaning e17 modules \033[0m\033[1m--------------------------\033[0m"
	build_each "e_modules/" "$e17_modules"
	echo -e "\033[1m--------------------------------------------------------------------------------\033[0m"
	echo

	clean=0
    fi
fi


# cvs
echo -e "\033[1m-------------------------------\033[7m CVS checkout/update \033[0m\033[1m----------------------------\033[0m"
if [ -z "$skip_cvsupdate" ]; then
	rm "$tmp_path/cvs_update.log" 2>/dev/null
	get_repo
else
	echo -e "\n                                - - - SKIPPED - - -\n"
fi
echo -e "\033[1m--------------------------------------------------------------------------------\033[0m"
echo

if [ "$action" == "update" ] && [ -e "$tmp_path/cvs_update.log" ]; then
	for update in `egrep "^[P|U] " "$tmp_path/cvs_update.log" | egrep "apps/|libs/|proto/" | cut -d'/' -f2 | sort -u`; do
		for package in $efl $apps; do
			if [ "$update" == "$package" ]; then
				only="$update $only"
			fi
		done
	done
	for update in `egrep "^[P|U] " "$tmp_path/cvs_update.log" | egrep -v "apps/|libs/|proto/" | cut -d'/' -f1 | cut -d' ' -f2 | sort -u`; do
		for package in $apps_misc $e17_modules; do
			if [ "$update" == "$package" ]; then
				only="$update $only"
			fi
		done
	done
fi

cnt_pkgs	# Count packages


echo -n "-> PREPARING FOR PHASE 2..."
set_title "Preparing for phase 2... compilation & installation"
sleep 5

logo 2
echo -e "\033[1m---------------------------\033[7m Installing libraries (EFL) \033[0m\033[1m-------------------------\033[0m"
pkg_pos=0
build_each "e17/" "$efl"
echo -e "\033[1m--------------------------------------------------------------------------------\033[0m"
echo

echo -e "\033[1m----------------------------\033[7m Installing applications \033[0m\033[1m---------------------------\033[0m"
build_each "e17/" "$apps"
build_each "misc/" "$apps_misc"
echo -e "\033[1m--------------------------------------------------------------------------------\033[0m"
echo

echo -e "\033[1m-----------------------------\033[7m Installing e17 modules \033[0m\033[1m---------------------------\033[0m"
build_each "e_modules/" "$e17_modules"
echo -e "\033[1m--------------------------------------------------------------------------------\033[0m"
echo 

# Restore current directory in case post processing wants to be pathless.
cd $EASY_PWD

echo -e "\033[1m-----------------------------\033[7m Finishing installation \033[0m\033[1m---------------------------\033[0m"
echo -n "- registering libraries ...... "
if [ -z "$asuser" ]; then
	case "$mode" in
		"sudo") echo "$sudopwd" | sudo -S nice -n $nice_level $ldconfig > /dev/null 2>&1 ;;
		*) nice -n $nice_level $ldconfig > /dev/null 2>&1 ;;
	esac
	echo "ok"
else
	echo "skipped"
fi
echo -n "- post install script ........ "
if [ "$easy_e17_post_script" ]; then
	echo -n " '$easy_e17_post_script' ... "
	case "$mode" in
		"sudo") echo "$sudopwd" | sudo -S nice -n $nice_level $easy_e17_post_script ;;
		*) nice -n $nice_level $easy_e17_post_script ;;
	esac
	echo "ok"
else	
	echo "skipped"
fi
echo -e "\033[1m--------------------------------------------------------------------------------\033[0m"
echo


echo -n "-> PREPARING FOR PHASE 3..."
set_title "Preparing for phase 3..."
sleep 5

logo 3
set_title "Finished"

for file in $logs_path/*.log ; do
	package=`basename "$file" | cut -d'.' -f1`
	if [ -e "$tmp_path/$package.installed" ]; then
		packages_installed="$packages_installed $package"
	else
		if [ -e "$tmp_path/$package.skipped" ]; then
			packages_skipped="$packages_skipped $package"
		else
			if [ -e "$tmp_path/$package.nobuild" ]; then
				packages_nobuild="$packages_nobuild $package"
			else
				packages_failed="$packages_failed $package"
			fi
		fi
	fi
done

echo -e "\033[1m--------------------------------\033[7m Cleaning temp dir \033[0m\033[1m-----------------------------\033[0m"
if [ -z "$keep" ]; then
	if [ "$packages_failed" ]; then
		echo -n "- saving logs ................ "	
		for package in $packages_installed; do
			rm "$tmp_path/$package.installed" 2>/dev/null
			rm "$logs_path/$package.log" 2>/dev/null
		done
	else
		echo -n "- deleting temp dir .......... "
		rm -rf $tmp_path 2>/dev/null
	fi	
	echo "ok"
else	
	echo "- saving temp dir ............ ok"
fi
echo -e "\033[1m--------------------------------------------------------------------------------\033[0m"
echo

if [ "$packages_failed" ]; then
	echo -e "\033[1m---------------------------------\033[7m Failed packages \033[0m\033[1m------------------------------\033[0m"
	for package in $packages_failed; do
		echo "- $package (error log: $logs_path/$package.log)"
	done
	echo -e "\033[1m--------------------------------------------------------------------------------\033[0m"
	echo 
fi		

if [ "$action" == "install" ]; then
	echo "INSTALL NOTES:"
	echo "-----------------------------------------------------------------------------"
	echo "The most incredible and really unbelivable dream has become true:"
	echo "You compiled e17 sucessfully!"
	echo 
	echo "Starting e17:"
	echo "Create a file ~/.xsession with the line 'exec $install_path/bin/enlightenment_start'."
	echo "Add a link to this file using 'ln -s ~/.xsession ~/.xinitrc'."
	echo
	echo "If you're using a login manager (GDM/KDM), select the session type 'default' in them."
	echo "If you're using the startx command, simply execute it now."
	echo
	echo "Note: e17 is still not released and it won't be in the near future. So don't"
	echo "ask for a stable release. e17 is still very buggy and only for experienced users"
	echo "who know what they do..."
	echo 
	echo "Rasterman didn't write this script so don't ask him for help with it."
	echo
	echo "Hint: From now on you can easily keep your installation up to date."
	echo "Simply run easy_e17.sh with -u instead of -i ."
	echo
	echo "We hope you will enjoy your trip into e17... Have fun!"
	echo -e "\033[1m--------------------------------------------------------------------------------\033[0m"
	echo
fi

# Clear this out if we ever set it.
export CC=""

# exit script or wait?
if [ "$wait" ]; then
	echo
	echo -e -n "\033[1mThe script is waiting here - simply press [enter] to exit.\033[0m"
	read
fi	

if [ "$packages_failed" ]; then
	exit 2
else
	exit 0
fi	
