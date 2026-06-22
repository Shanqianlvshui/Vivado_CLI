puts "VIVADO_MCP_GUI_SMOKE_BEGIN"
puts "version=[version -short]"
after 7000 {
    puts "VIVADO_MCP_GUI_SMOKE_STOP"
    catch { stop_gui }
    exit
}
puts "starting_gui"
start_gui
puts "gui_started_or_returned"
vwait forever
