def script_handler(working_directory, file_name):

    try:
        filepath = os.path.join(working_directory, 'downloadandchunk', file_name)
        count = 2000000
        data = read_file(filepath, count)

        try:
            # if placement passes without issue, go to multiple sensor processing
            sensors = 3
            data_sub = copy.copy(data.loc[:2000])
            shift_accel(data_sub)
            placement = detect_placement(data_sub)

            # if placement passed, check to see if any sensor fell down or data missing for
            # any of the sensors
            truncated, single_sensor, index = detect_data_truncation(data, placement)
            if truncated:
                if index < 2000:
                    print('File too short after truncation. Stopping execution')
                    raise PlacementDetectionException('File too short after truncation.')
                else:
                    print('Truncated')
                    tmp_filename = filepath + '_tmp'
                    # truncate combined file at lines where truncation was detected
                    os.system(
                        'head -c {bytes} {filepath} > {truncated_filename}'.format(
                            bytes=(index) * 40,
                            filepath=filepath,
                            truncated_filename=tmp_filename
                            )
                        )
                    # copy tmp_file to replace the original file
                    os.system('cat {tmp_filename} > {filepath}'.format(
                        tmp_filename=tmp_filename,
                        filepath=filepath))
                    # finally delete temporary file
                    os.remove(tmp_filename)
            elif single_sensor:
                print('single Sensor')
                sensors = 1

            body_frame_transforms = compute_transform(data_sub, placement, sensors)

            return {
                'Placement': placement,
                'BodyFrameTransforms': {
                    'Left': body_frame_transforms[0],
                    'Hip': body_frame_transforms[1],
                    'Right': body_frame_transforms[2],
                },
                'HipNeutralYaw': body_frame_transforms[3],
                'Sensors' : sensors
            }

        except PlacementDetectionException as err:
            print(err)
            # if it fails, assign a placement, get transform values and go
            # to single sensor processing
            sensors = 1
            # detect the single sensor being used
            placement = detect_single_sensor(data)
            truncated, single_sensor, index = detect_data_truncation(data, placement, sensors)
            if truncated:
                if index <= 2000:
                    print('File too short after truncation. Stopping execution')
                    raise PlacementDetectionException('File too short after truncation.')
                else:
                    print('Truncated')
                    tmp_filename = filepath + '_tmp'
                    # truncate combined file at lines where truncation was detected
                    os.system(
                        'head -c {bytes} {filepath} > {truncated_filename}'.format(
                            bytes=(index) * 40,
                            filepath=filepath,
                            truncated_filename=tmp_filename
                            )
                        )
                    # copy tmp_file to replace the original file
                    os.system('cat {tmp_filename} > {filepath}'.format(
                        tmp_filename=tmp_filename,
                        filepath=filepath))
                    # finally delete temporary file
                    os.remove(tmp_filename)
                
            # get transformation values
            data_sub = copy.copy(data.loc[0:2000, :])
            shift_accel(data_sub)
            body_frame_transforms = compute_transform(data_sub, placement, sensors)

            return {
                'Placement': placement,
                'BodyFrameTransforms': {
                    'Left': body_frame_transforms[0],
                    'Hip': body_frame_transforms[1],
                    'Right': body_frame_transforms[2],
                },
                'HipNeutralYaw': body_frame_transforms[3],
                'Sensors' : sensors
            }

    except Exception as error:
        print(error)
        print('Process did not complete successfully! See error below!')
        raise
