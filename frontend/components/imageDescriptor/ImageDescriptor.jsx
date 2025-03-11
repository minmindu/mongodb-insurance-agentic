"use client";

import { useState } from "react";
import styles from "./imageDescriptor.module.css";

const ImageDescriptor = () => {
  const [droppedImage, setDroppedImage] = useState(null);
  const [imagePreview, setImagePreview] = useState(null);
  const [similarDocs, setSimilarDocs] = useState([]);
  const [loading, setLoading] = useState(false);

  const handleDragOver = (e) => e.preventDefault();

  const handleDrop = (e) => {
    e.preventDefault();
    const file = e.dataTransfer.files[0];
    if (file) {
      setDroppedImage(file);
      
      // Generate image preview
      const reader = new FileReader();
      reader.onload = (event) => setImagePreview(event.target.result);
      reader.readAsDataURL(file);
    }
  };

  const handleUpload = async () => {
    if (!droppedImage) {
      alert("Please drop an image first.");
      return;
    }

    const apiUrl = process.env.NEXT_PUBLIC_IMAGE_DESCRIPTOR_API_URL;
    setLoading(true);

    const formData = new FormData();
    formData.append("file", droppedImage);

    try {
      const response = await fetch(apiUrl, {
        method: "POST",
        body: formData,
      });

      if (!response.body) {
        throw new Error("ReadableStream not yet supported in this browser.");
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let done = false;

      while (!done) {
        const { value, done: doneReading } = await reader.read();
        done = doneReading;

        const chunk = decoder.decode(value, { stream: true });
        console.log("Received chunk:", chunk);

        setSimilarDocs((prev) => [...prev, chunk]);
      }
    } catch (error) {
      console.error("Error while streaming response:", error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className={styles.content}>
      <div className={styles.imageDescriptorSection}>
        <h2>Image Search</h2>

        <div
          className={styles.dragBox}
          onDragOver={handleDragOver}
          onDrop={handleDrop}
        >
          {imagePreview ? (
            <img
              className={styles.droppedImage}
              src={imagePreview}
              alt="Dropped"
            />
          ) : (
            <p className={styles.dragText}>Drag & Drop your image here</p>
          )}
        </div>

        <button
          className={styles.uploadBtn}
          onClick={handleUpload}
          disabled={loading}
        >
          {loading ? <div className={styles.spinner}></div> : "Upload Photo"}
        </button>
      </div>

      <div className={styles.similarImageSection}>
        <h2>Live Response</h2>
        <div className={styles.similarDocsContainer}>
          {similarDocs.map((doc, index) => (
            <p key={index} className={styles.similarDoc}>
              {doc}
            </p>
          ))}
        </div>
      </div>
    </div>
  );
};

export default ImageDescriptor;
