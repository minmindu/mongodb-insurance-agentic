"use client";

import { useState, useEffect } from "react";
import styles from "./imageDescriptor.module.css";
import Button from "@leafygreen-ui/button";
import Modal from "@leafygreen-ui/modal";
import UserCard from "../userCard/UserCard";
import { Subtitle } from "@leafygreen-ui/typography";


const ImageDescriptor = () => {
  const [droppedImage, setDroppedImage] = useState(null);
  const [imagePreview, setImagePreview] = useState(null);
  const [similarDocs, setSimilarDocs] = useState([]);
  const [loading, setLoading] = useState(false);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [selectedImage, setSelectedImage] = useState(null);
  const [sampleImages, setSampleImages] = useState([]);

  useEffect(() => {
    const fetchSampleImages = async () => {
      try {
        const response = await fetch("/api/getSampleImages");
        const data = await response.json();
        setSampleImages(data.images);
      } catch (error) {
        console.error("Error fetching sample images:", error);
      }
    };
    fetchSampleImages();
  }, []);

  const handleDragOver = (e) => e.preventDefault();

  const handleDrop = (e) => {
    e.preventDefault();
    const file = e.dataTransfer.files[0];
    if (file) {
      setDroppedImage(file);
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

    setLoading(true);
    const formData = new FormData();
    formData.append("file", droppedImage);
    try {
      const response = await fetch(process.env.NEXT_PUBLIC_IMAGE_DESCRIPTOR_API_URL, {
        method: "POST",
        body: formData,
      });
      if (!response.body) throw new Error("ReadableStream not supported.");
      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let done = false;
      while (!done) {
        const { value, done: doneReading } = await reader.read();
        done = doneReading;
        setSimilarDocs((prev) => [...prev, decoder.decode(value, { stream: true })]);
      }
    } catch (error) {
      console.error("Error while streaming response:", error);
    } finally {
      setLoading(false);
    }
  };

  const handleImageSelect = (image) => setSelectedImage(image);
  const handleConfirmSelection = () => {
    if (selectedImage) {
      setImagePreview(selectedImage);
      setDroppedImage(selectedImage);
      setIsModalOpen(false);
    }
  };

  return (
    <div className={styles.content}>
      <div className={styles.imageDescriptorSection}>

        <UserCard name="Luca Napoli" role="Leafy Insurance Customer" image="/assets/eddie.png" />

        <h2>Image Search</h2>

        <div
          className={styles.dragBox}
          onDragOver={handleDragOver}
          onDrop={handleDrop}
        >
          {imagePreview ? (
            <img className={styles.droppedImage} src={imagePreview} alt="Selected" />
          ) : (
            <p className={styles.dragText}>Drag & Drop your image here</p>
          )}
        </div>

        <Button className={styles.uploadBtn} variant="primary" onClick={handleUpload} disabled={loading}>
          {loading ? <div className={styles.spinner}></div> : "Upload and Generate Description"}
        </Button>

        <p className={styles.link} onClick={() => setIsModalOpen(true)}>Choose from sample images</p>

        <div className={styles.imageDescription}>

          <Subtitle className={styles.subtitle}>AI generated image description</Subtitle>

          <div className={styles.similarDocsContainer}>
            {similarDocs.map((doc, index) => (
              <p key={index} className={styles.similarDoc}>{doc}</p>
            ))}
          </div>

        </div>

      </div>

      <Modal open={isModalOpen} setOpen={setIsModalOpen}>
        <h3>Choose from the sample images</h3>
        <div className={styles.imageGrid}>
          {sampleImages.map((image, index) => (
            <img
              key={index}
              src={`/sample_photos/${image}`}
              alt={`Sample ${index + 1}`}
              className={selectedImage === `/sample_photos/${image}` ? styles.selectedImage : styles.sampleImage}
              onClick={() => handleImageSelect(`/sample_photos/${image}`)}
            />
          ))}
        </div>
        <Button variant="primary" onClick={handleConfirmSelection} className={styles.confirmButtonContainer}>Confirm Selection</Button>
      </Modal>



      <div className={styles.similarImageSection}>

        <UserCard name="Mark Scout" role="Claim Adjuster" image="/assets/rob.png" />

        <h2>xxx</h2>
      </div>
    </div>
  );
};

export default ImageDescriptor;
