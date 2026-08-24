import functions as fn
from nicegui import app, ui


app.on_startup(fn.handle_startup)

with ui.row():
    ui.label('Control').classes('text-h4')
    ui.button("START", on_click=lambda:fn.connect())


with ui.row():
    with ui.card().style('width:620px;height:600px;'):
        ui.label('Camera')
        camera_image = ui.interactive_image().style('width:620px;height:480px;')
        ui.button('TAKE PICTURE', on_click=fn.takePic).classes('w-full')

    with ui.card().style('width:620px;height:600px;'):
        ui.label('SPECTROMETER PLOT')
        plot_ui = ui.plotly({
            'data': [{
              'x': [],
              'y': [],
              'type': 'scatter',
              'mode': 'lines',
              'line': {'color': 'blue', 'width': 1},
            }],
            'layout': {
              'margin': {'l': 40, 'r': 20, 't': 20, 'b': 40},
              'xaxis': {'title': 'Wavelength (nm)'},
              'yaxis': {'title': 'Intensity (counts)'},
              'uirevision': 'true',
            },
        }).classes('w-full h-full')
        with ui.row():
            ui.button("TAKE BACKGROUND", on_click=fn.take_bkg)
            ui.button("TAKE SPECTRUM", on_click=fn.take_sp)
            ui.button("INTEGRATION TIME", on_click=fn.set_integration_time_dialog)

    with ui.column():

        with ui.card().style('width:375px;height:300px;'):
            ui.label('SCAN DATA')
            with ui.row():
                ui.number(label='ΔX - MICROMETERS').bind_value(fn.state, 'deltaX')
                ui.number(label='ΔY - MICROMETERS').bind_value(fn.state, 'deltaY')
            with ui.row():
                ui.number(label='Nx').bind_value(fn.state, 'nx')
                ui.number(label='Ny').bind_value(fn.state, 'ny')
            with ui.row():
                ui.button('SPECTROMETER SCAN', on_click=fn.specroScan_live)

        with ui.card().style('width:375px;height:270px;'):
            ui.label('Current Position')
            x_label = ui.label("Stepper X: 0.0000 mm")
            y_label = ui.label("Stepper Y: 0.0000 mm")
            z_label = ui.label("Stepper Z: 0.0000 mm")
            px_label = ui.label("Piezo X: 0.0000 mm")
            py_label = ui.label("Piezo Y: 0.0000 mm")
            pz_label = ui.label("Piezo Z: 0.0000 mm")

with ui.row():
        with ui.column():
            with ui.card():
                ui.label('STEPPER CONTROL')

                with ui.row():
                    with ui.column():
                        with ui.row():
                            ui.label('        ')
                            ui.label('Relative').classes('text-h6')
                            ui.label('        ')
                            ui.label('        ')
                            ui.label('        ')
                            ui.label('Absolute').classes('text-h6')

                        with ui.row():
                            ui.label('x')
                            ui.number(label='Xrel').bind_value(fn.state, 'xrel').classes('text-h8')
                            ui.checkbox().bind_value(fn.state, 'chx')
                            ui.number(label='Xabs').bind_value(fn.state, 'xabs').classes('text-h8')

                        with ui.row():
                            ui.label('y')
                            ui.number(label='Yrel').bind_value(fn.state, 'yrel').classes('text-h8')
                            ui.checkbox().bind_value(fn.state, 'chy')
                            ui.number(label='Yabs').bind_value(fn.state, 'yabs').classes('text-h8')

                        with ui.row():
                            ui.label('z')
                            ui.number(label='Zrel').bind_value(fn.state, 'zrel').classes('text-h8')
                            ui.checkbox().bind_value(fn.state, 'chz')
                            ui.number(label='Zabs').bind_value(fn.state, 'zabs').classes('text-h8')

                    with ui.column():
                        with ui.row():
                            ui.button('<', on_click=fn.moverelneg).style('width:40px;height:20px;')
                            ui.button('>', on_click=fn.moverelpos).style('width:40px;height:20px;')
                            ui.button('ABS', on_click=fn.moveabs).style('width:40px;height:20px;')

                        ui.button('home', on_click=fn.homeLaComanda).style('width:120px;height:40px;')
                        ui.button('stop', on_click=fn.noMoreMove).style('width:120px;height:40px;')

        with ui.column():

            with ui.card():
                ui.label('PIEZO CONTROL')
                mode_toggle = ui.toggle(['voltage (v)', 'position (µm)'], value='voltage (v)')

                with ui.row():
                    ui.label('axis')
                    ui.label('target value')

                with ui.row():
                    ui.label('x')
                    ui.number(label='x target', value=0.0, format='%.2f').bind_value(fn.state, 'pzt_x_val')
                    ui.button('set x', on_click=lambda:fn.set_piezo('x', mode_toggle.value)).style('width:70px;')

                with ui.row():
                    ui.label('y')
                    ui.number(label='y target', value=0.0, format='%.2f').bind_value(fn.state, 'pzt_y_val')
                    ui.button('set y', on_click=lambda:fn.set_piezo('y', mode_toggle.value)).style('width:70px;')

                with ui.row():
                    ui.label('z')
                    ui.number(label='z target', value=0.0, format='%.2f').bind_value(fn.state, 'pzt_z_val')
                    ui.button('set z', on_click=lambda:fn.set_piezo('z', mode_toggle.value)).style('width:70px;')

                with ui.row():
                    ui.button('zero all', on_click=lambda:fn.zero_piezo_all(mode_toggle.value)).style('width:110px; height:40px;').props('color=warning')
                    ui.button('set all', on_click=lambda:fn.set_piezo_all(mode_toggle.value)).style('width:110px; height:40px;')


def refresh_x_display():
    x_label.text = f"Stepper X: {fn.state['x_live_pos']:.4f} mm"
    y_label.text = f"Stepper Y: {fn.state['y_live_pos']:.4f} mm"
    z_label.text = f"Stepper Z: {fn.state['z_live_pos']:.4f} mm"
    px_label.text = f"Piezo X: {fn.state['pzt_x_live']:.4f} mm"
    py_label.text = f"Piezo Y: {fn.state['pzt_y_live']:.4f} mm"
    pz_label.text = f"Piezo Z: {fn.state['pzt_z_live']:.4f} mm"


camera_timer = ui.timer(0.05, lambda: fn.update_camera(camera_image))

ui.timer(0.2, fn.update_live_positions)

ui.timer(0.2, refresh_x_display)

ui.timer(0.1, lambda: fn.update_plot(plot_ui))

fn.camera_timer = camera_timer

ui.run()
