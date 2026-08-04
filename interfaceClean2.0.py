import functions as fn
from nicegui import app, ui

# Register startup handler
app.on_startup(fn.handle_startup)

ui.label('Control').classes('text-h4')

# =========================================================================
# TOP ROW: CAMERA, PLOT, TELEMETRY
# =========================================================================
with ui.row():
  with ui.card():
    ui.label('Camera')
    camera_image = ui.interactive_image().style('width:620px;height:480px;')
    ui.button('TAKE PIC', on_click=fn.takePic).classes('w-full')

  with ui.card().style('width:620px;height:520px;'):
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

  with ui.card().style('width:300px;height:480px;'):
    ui.label('telemetry')
    ui.button('START', on_click=fn.connect)
    ui.label('info care vine mai tarziu')

# =========================================================================
# BOTTOM ROW: STEPPER, PIEZO, SPECTROMETER
# =========================================================================
with ui.row():
  with ui.card():
    ui.label('Stepper Control')
    with ui.row():
      ui.label('        ')
      ui.label('Relative').classes('text-h5')
      ui.label('        ')
      ui.label('        ')
      ui.label('        ')
      ui.label('Absolute').classes('text-h5')

    with ui.row():
      ui.label('X')
      ui.number(label='xRel').bind_value(fn.state, 'xRel')
      ui.checkbox().bind_value(fn.state, 'chx')
      ui.number(label='xAbs').bind_value(fn.state, 'xAbs')

    with ui.row():
      ui.label('Y')
      ui.number(label='yRel').bind_value(fn.state, 'yRel')
      ui.checkbox().bind_value(fn.state, 'chy')
      ui.number(label='yAbs').bind_value(fn.state, 'yAbs')

    with ui.row():
      ui.label('Z')
      ui.number(label='zRel').bind_value(fn.state, 'zRel')
      ui.checkbox().bind_value(fn.state, 'chz')
      ui.number(label='zAbs').bind_value(fn.state, 'zAbs')

    with ui.row():
      ui.label('        ')
      ui.button('<', on_click=fn.moverelneg).style('width:40px;height:40px;')
      ui.button('>', on_click=fn.moverelpos).style('width:40px;height:40px;')
      ui.label('        ')
      ui.label('        ')
      ui.label('        ')
      ui.button('ABS', on_click=fn.moveabs).style('width:40px;height:40px;')

    with ui.row():
      ui.button('HOME', on_click=fn.homeLaComanda).style(
          'width:120px;height:40px;'
      )
      ui.button('STOP', on_click=fn.noMoreMove).style(
          'width:120px;height:40px;'
      )

  with ui.card():
    ui.label('Piezo Control')

    mode_toggle = ui.toggle(
        ['Voltage (V)', 'Position (µm)'], value='Voltage (V)'
    )

    with ui.row():
      ui.label('Axis')
      ui.label('Target Value')

    with ui.row():
      ui.label('X')
      ui.number(label='X Target', value=0.0, format='%.2f').bind_value(
          fn.state, 'pzt_x_val'
      )
      ui.button(
          'SET X', on_click=lambda: fn.set_piezo('X', mode_toggle.value)
      ).style('width:70px;')

    with ui.row():
      ui.label('Y')
      ui.number(label='Y Target', value=0.0, format='%.2f').bind_value(
          fn.state, 'pzt_y_val'
      )
      ui.button(
          'SET Y', on_click=lambda: fn.set_piezo('Y', mode_toggle.value)
      ).style('width:70px;')

    with ui.row():
      ui.label('Z')
      ui.number(label='Z Target', value=0.0, format='%.2f').bind_value(
          fn.state, 'pzt_z_val'
      )
      ui.button(
          'SET Z', on_click=lambda: fn.set_piezo('Z', mode_toggle.value)
      ).style('width:70px;')

    with ui.row():
      ui.button(
          'ZERO ALL', on_click=lambda: fn.zero_piezo_all(mode_toggle.value)
      ).style('width:110px; height:40px;').props('color=warning')
      ui.button(
          'SET ALL', on_click=lambda: fn.set_piezo_all(mode_toggle.value)
      ).style('width:110px; height:40px;')

  with ui.card():
    ui.label('Spectrometer')
    ui.button(
        'INTEG.TIME', on_click=lambda: fn.set_integration_time_dialog()
    ).style('width:200px;height:60px;')
    ui.button('TAKE.BKG', on_click=lambda: fn.take_bkg()).style(
        'width:200px;height:60px;'
    )
    ui.button('TAKE.SP', on_click=lambda: fn.take_sp()).style(
        'width:200px;height:60px;'
    )

# =========================================================================
# REFRESH TIMERS
# =========================================================================
camera_timer = ui.timer(0.05, lambda: fn.update_camera(camera_image))
ui.timer(0.1, lambda: fn.update_plot(plot_ui))

# Store camera timer reference globally for enable/disable during init
fn.camera_timer = camera_timer

ui.run()