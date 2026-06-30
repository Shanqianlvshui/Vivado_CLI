set script_dir [file dirname [file normalize [info script]]]
set session_dir [file normalize [expr {[llength $argv] >= 1 ? [lindex $argv 0] : [file join $script_dir ".." ".vivado_cli_session"]}]]
set open_gui [expr {[lsearch -exact $argv "--gui"] >= 0}]

set inbox_dir [file join $session_dir "inbox"]
set running_dir [file join $session_dir "running"]
set done_dir [file join $session_dir "done"]
file mkdir $session_dir $inbox_dir $running_dir $done_dir

proc cli_write_text {path text} {
    set f [open $path w]
    puts -nonewline $f $text
    close $f
}

proc cli_now {} {
    return [clock format [clock seconds] -format {%Y-%m-%dT%H:%M:%S%z}]
}

proc cli_status {state detail} {
    global session_dir
    cli_write_text [file join $session_dir "status.txt"] "state=$state\ntime=[cli_now]\ndetail=$detail\n"
}

proc cli_gui_status {state detail {code ""} {result ""}} {
    global session_dir
    set text "state=$state\ntime=[cli_now]\ndetail=$detail\n"
    if {$code ne ""} {
        append text "code=$code\n"
    }
    if {$result ne ""} {
        append text "result=$result\n"
    }
    cli_write_text [file join $session_dir "gui_status.txt"] $text
}

proc cli_run_command_file {command_file} {
    global running_dir done_dir

    set name [file tail $command_file]
    set stem [file rootname $name]
    set running_file [file join $running_dir $name]
    set result_file [file join $done_dir "${stem}.result.txt"]

    file rename -force $command_file $running_file
    cli_status "busy" $name

    set started [cli_now]
    set code [catch {uplevel #0 [list source $running_file]} result options]
    set finished [cli_now]

    set output "command=$name\nstarted=$started\nfinished=$finished\ncode=$code\n"
    append output "result=$result\n"
    if {$code != 0} {
        append output "errorinfo=[dict get $options -errorinfo]\n"
    }
    cli_write_text $result_file $output
    cli_status "idle" "completed $name"
}

proc cli_poll {} {
    global inbox_dir
    set files [lsort [glob -nocomplain -directory $inbox_dir *.tcl]]
    foreach command_file $files {
        if {[file exists $command_file]} {
            cli_run_command_file $command_file
        }
    }
    after 250 cli_poll
}

cli_status "starting" "bridge loaded"

if {$open_gui} {
    cli_gui_status "requested" "start_gui scheduled"
    after 0 {
        set gui_code [catch {
            start_gui
        } gui_result]
        if {$gui_code == 0} {
            cli_gui_status "started" "start_gui returned" $gui_code $gui_result
        } else {
            cli_gui_status "error" "start_gui failed" $gui_code $gui_result
        }
    }
} else {
    cli_gui_status "not_requested" "session started without GUI"
}

cli_status "idle" "ready"
cli_poll
if {!$open_gui} {
    vwait ::vivado_cli_bridge_forever
}
