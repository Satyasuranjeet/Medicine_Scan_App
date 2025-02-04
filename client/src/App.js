import React, { useState } from 'react';
import axios from 'axios';
import { Camera } from 'lucide-react';

const App = () => {
  const [image, setImage] = useState(null);
  const [medicineInfo, setMedicineInfo] = useState(null);
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(false);

  const handleImageUpload = async (event) => {
    const file = event.target.files[0];
    setImage(URL.createObjectURL(file));
    setLoading(true);
    setError(null);

    const formData = new FormData();
    formData.append('file', file);

    try {
      const response = await axios.post('http://127.0.0.1:5000/scan-medicine', formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });

      if (response.data.status === 'success') {
        setMedicineInfo(response.data.medicine);
      } else {
        setError(response.data.message);
      }
    } catch (err) {
      setError('Error scanning medicine. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-md mx-auto p-4">
      <h1 className="text-2xl font-bold mb-4">Medicine Scanner</h1>
      
      <input 
        type="file" 
        accept="image/*" 
        onChange={handleImageUpload} 
        className="hidden" 
        id="medicine-upload"
      />
      
      <label 
        htmlFor="medicine-upload" 
        className="flex items-center justify-center w-full p-4 border-2 border-dashed cursor-pointer hover:bg-gray-100"
      >
        <Camera className="mr-2" />
        Upload Medicine Image
      </label>

      {image && (
        <div className="mt-4">
          <img src={image} alt="Uploaded medicine" className="w-full rounded" />
        </div>
      )}

      {loading && <p className="text-center mt-4">Scanning image...</p>}

      {error && (
        <div className="mt-4 p-2 bg-red-100 text-red-700 rounded">
          {error}
        </div>
      )}

      {medicineInfo && (
        <div className="mt-4 p-4 bg-blue-50 rounded">
          <h2 className="text-xl font-semibold mb-2">{medicineInfo.name}</h2>
          <p><strong>Uses:</strong> {medicineInfo.uses}</p>
          <p><strong>Dosage:</strong> {medicineInfo.dosage}</p>
          <p><strong>Side Effects:</strong> {medicineInfo.side_effects}</p>
          <p><strong>Precautions:</strong> {medicineInfo.precautions}</p>
        </div>
      )}
    </div>
  );
};

export default App;
