import { useState, useEffect, useRef } from 'react';
import * as tf from '@tensorflow/tfjs';
import * as mobilenet from '@tensorflow-models/mobilenet';

export default function tensorflowbrowser() {
  const [isModelLoading, setIsModelLoading] = useState(true);
  const [model, setModel] = useState(null);
  const [prediction, setPrediction] = useState([]);
  const imageRef = useRef();

  // Load the model on mount
  useEffect(() => {
    const loadModel = async () => {
      setIsModelLoading(true);
      try {
        // Initialize TFJS (optional but good for debugging)
        await tf.ready();
        const loadedModel = await mobilenet.load();
        setModel(loadedModel);
        console.log("Model loaded successfully!");
      } catch (error) {
        console.error("Error loading model:", error);
      }
      setIsModelLoading(false);
    };
    loadModel();
  }, []);

  const identifyImage = async () => {
    if (model && imageRef.current) {
      const results = await model.classify(imageRef.current);
      setPrediction(results);
    }
  };

  return (
    <div style={{ textAlign: 'center', padding: '20px' }}>
      
      
      {isModelLoading ? (
        <h2>Loading Model</h2>
      ) : (
        <>
          <div style={{ marginBottom: '20px' }}>
            <img 
              src="https://images.dog.ceo/breeds/retriever-golden/n02099601_3004.jpg" 
              alt="Classifier Source" 
              crossOrigin="anonymous" 
              ref={imageRef}
              style={{ width: '300px', borderRadius: '10px' }}
            />
          </div>
          
          <button onClick={identifyImage} style={{ padding: '10px 20px', fontSize: '16px' }}>
            Identify Image
          </button>

          <div style={{ marginTop: '20px' }}>
            {prediction.map((p, index) => (
              <p key={index}>
                <strong>{p.className}</strong>: {(p.probability * 100).toFixed(2)}%
              </p>
            ))}
          </div>
        </>
      )}
    </div>
  );
}

