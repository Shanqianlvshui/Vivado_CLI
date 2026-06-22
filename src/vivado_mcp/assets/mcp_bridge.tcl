set script_dir [file dirname [file normalize [info script]]]
set session_dir [file normalize [expr {[llength $argv] >= 1 ? [lindex $argv 0] : [file join $script_dir ".." ".vivado_mcp_session"]}]]
set open_gui [expr {[lsearch -exact $argv "--gui"] >= 0}]

set inbox_dir [file join $session_dir "inbox"]
set running_dir [file join $session_dir "running"]
set done_dir [file join $session_dir "done"]
file mkdir $session_dir $inbox_dir $running_dir $done_dir

proc mcp_write_text {path text} {
    set f [open $path w]
    puts -nonewline $f $text
    close $f
}

proc mcp_now {} {
    return [clock format [clock seconds] -format {%Y-%m-%dT%H:%M:%S%z}]
}

proc mcp_status {state detail} {
    global session_dir
    mcp_write_text [file join $session_dir "status.txt"] "state=$state\ntime=[mcp_now]\ndetail=$detail\n"
}

proc mcp_run_command_file {command_file} {
    global running_dir done_dir

    set name [file tail $command_file]
    set stem [file rootname $name]
    set running_file [file join $running_dir $name]
    set result_file [file join $done_dir "${stem}.result.txt"]

    file rename -force $command_file $running_file
    mcp_status "busy" $name

    set started [mcp_now]
    set code [catch {uplevel #0 [list source $running_file]} result options]
    set finished [mcp_now]

    set output "command=$name\nstarted=$started\nfinished=$finished\ncode=$code\n"
    append output "result=$result\n"
    if {$code != 0} {
        append output "errorinfo=[dict get $options -errorinfo]\n"
    }
    mcp_write_text $result_file $output
    mcp_status "idle" "completed $name"
}

proc mcp_poll {} {
    global inbox_dir
    set files [lsort [glob -nocomplain -directory $inbox_dir *.tcl]]
    foreach command_file $files {
        if {[file exists $command_file]} {
            mcp_run_command_file $command_file
        }
    }
    after 250 mcp_poll
}

mcp_status "starting" "bridge loaded"

if {$open_gui} {
    after 0 {
        catch {
            start_gui
        } gui_result
    }
}

mcp_status "idle" "ready"
mcp_poll
vwait ::vivado_mcp_bridge_forever

