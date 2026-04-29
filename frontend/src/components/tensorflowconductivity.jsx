import { useState, useEffect, useRef } from 'react';
import * as tf from '@tensorflow/tfjs';
import * as mobilenet from '@tensorflow-models/mobilenet';

import {sensor_data,TARGET_SENSOR_IDS} from './testCard'

export default function TensorflowConductivity() {

useEffect(() => {
    console.log(sensor_data.sensorDataMap);
    console.log(sensor_data.activeSensors);

    console.log(TARGET_SENSOR_IDS);

}, [])

return (<div style={{ padding: '20px' }}>
    <h3>Target Sensor IDs:</h3>
      <ul>
        {TARGET_SENSOR_IDS.map((id) => (
          <li key={id}>{id}</li>
        ))}
      </ul>
</div>);
}