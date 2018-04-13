def get_single_sensor_data(data, hip_sensor):
    """Subset data to only use the single sensor used
    """
    columns = ['epoch_time',
               'magn_'+str(hip_sensor), 'corrupt_'+str(hip_sensor),
               'aX'+str(hip_sensor), 'aY'+str(hip_sensor), 'aZ'+str(hip_sensor),
               'qX'+str(hip_sensor), 'qY'+str(hip_sensor), 'qZ'+str(hip_sensor), 'qW'+str(hip_sensor)]
    single_sensor_data = data.loc[:, columns]
    single_sensor_data.columns = ['epoch_time',
                                  'magn', 'corrupt',
                                  'aX', 'aY', 'aZ',
                                  'qX', 'qY', 'qZ', 'qW']
    return single_sensor_data

