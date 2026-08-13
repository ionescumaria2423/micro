# def specroScan():
#   nx = int(state['nx'])
#   ny = int(state['ny'])
#
#   delta_x = state['deltaX']
#   delta_y = state['deltaY']
#
#   step_x = Decimal(delta_x/nx)
#   step_y = Decimal(delta_y/ny)
#
#   sx = Decimal(float(delta_x/nx)*0.01)
#   sy = Decimal(float(delta_y/ny)*0.01)
#
#   s=Decimal(float(delta_x//3))
#   d=Decimal(float(delta_y//3))
#
#   a=Decimal(float(delta_x%3))
#   b=Decimal(float(delta_y%3))
#
#   print(f"Starting Scan: nx={nx}, ny={ny}, deltaX={delta_x}, deltaY={delta_y}")
#
#
#   if delta_x <= 4 or delta_y <= 4:
#     for i in range(ny):
#
#
#       for j in range(nx):
#         target_x = Decimal(j * (delta_x / nx if nx > 1 else 0))
#         print(f" -> Moving Piezo X to: {target_x}")
#         PiezoCH_X.SetPosition(target_x)
#         time.sleep(0.05)
#
#       target_y = Decimal(i * (delta_y / ny if ny > 1 else 0))
#       print(f"Moving Piezo Y to: {target_y}")
#       PiezoCH_Y.SetPosition(target_y)
#       time.sleep(0.05)
#
#
#
# elif delta_x > 4 and delta_y > 4 and sx>=0.6 and sy>=0.6:
  # else:
  #   for i in range(ny):
  #     for j in range(nx):
  #
  #       CH_X.MoveRelative(MotorDirection.Forward, sx, timeout)
  #       time.sleep(0.05)
  #
  #     CH_Y.MoveRelative(MotorDirection.Forward, sy, timeout)
  #
  #     CH_X.MoveRelative(MotorDirection.Backward, Decimal(float(delta_x) * 0.01), timeout)
  #     time.sleep(0.05)


  #else:
  #   n=PiezoCH_X.get_position()
  #   m=PiezoCH_Y.get_position()
  #   s=CH_X.get_position
  #   for i in range (ny):
  #     for j in range (nx):
  #
  #       if (PiezoCH_X.get_position() + step_x)>3:
  #         a=3-PiezoCH_X.get_position()
  #         PiezoCH_X.SetPosition(n)
  #         CH_X.MoveRelative(MotorDirection.Forward, 0.03, timeout)
  #         PiezoCH_X.SetPosition(PiezoCH_X.get_position() + step_x - a)
  #         time.sleep(0.05)
  #
  #       elif(CH_X.get_position() * 0.01 + step_x > delta_x):
  #         PiezoCH_X.SetPosition(n)
  #         CH_X.MoveTo(s, timeout)
  #         time.sleep(0.05)
  #
  #       else:
  #         PiezoCH_X.SetPosition(PiezoCH_X.get_position + step_x)
  #         time.sleep(0.05)