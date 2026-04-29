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

return (<div>
    <h2>TensorFlow Conductivity Component</h2>
    <p>This component is set up to work with TensorFlow.js and the conductivity sensor data.</p>
    <p>Check the console for the loaded sensor data and target sensor IDs.</p>
</div>);
}