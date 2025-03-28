"use client";

import { useState, useEffect } from "react";
import styles from "./imageDescriptor.module.css";
import Button from "@leafygreen-ui/button";
import Modal from "@leafygreen-ui/modal";
import UserCard from "../userCard/UserCard";
import { Subtitle, Body } from "@leafygreen-ui/typography";
import Icon from "@leafygreen-ui/icon";
import Badge from "@leafygreen-ui/badge";
import ToastNotification from "../toastNotification/ToastNotification";

const ImageDescriptor = () => {
  const [droppedImage, setDroppedImage] = useState(null);
  const [imagePreview, setImagePreview] = useState(null);
  const [similarDocs, setSimilarDocs] = useState([]);
  const [loading, setLoading] = useState(false);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [selectedImage, setSelectedImage] = useState(null);
  const [sampleImages, setSampleImages] = useState([]);
  const [showDescription, setShowDescription] = useState(false);
  const [showToast, setShowToast] = useState(false);
  const [claimDetails, setClaimDetails] = useState(null);

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

  useEffect(() => {
    const fetchClaimDetails = async () => {
      try {
        const response = await fetch("/api/fetchData");
        const data = await response.json();
        setClaimDetails(data); 
      } catch (error) {
        console.error("Error fetching claim details:", error);
      }
    };
    fetchClaimDetails();
  }, []);

  const handleDragOver = (e) => e.preventDefault();

  const handleDrop = (e) => {
    e.preventDefault();
    const file = e.dataTransfer.files[0];
    if (file) {
      setDroppedImage(file);
      setSelectedImage(null);
      setShowDescription(false);
      const reader = new FileReader();
      reader.onload = (event) => setImagePreview(event.target.result);
      reader.readAsDataURL(file);
    }
  };

  const handleUpload = async () => {
    if (!droppedImage && !selectedImage) {
      alert("Please select or drop an image first.");
      return;
    }

    setLoading(true);
    setShowDescription(false);
    setShowToast(false);

    const formData = new FormData();

    if (droppedImage) {
      formData.append("file", droppedImage);
    } else {
      const response = await fetch(selectedImage);
      const blob = await response.blob();
      const file = new File([blob], "selectedImage.jpg", { type: blob.type });
      formData.append("file", file);
    }

    try {
      const response = await fetch(process.env.NEXT_PUBLIC_IMAGE_DESCRIPTOR_API_URL, {
        method: "POST",
        body: formData,
      });

      if (!response.body) throw new Error("ReadableStream not supported.");

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let done = false;
      let resultText = [];

      while (!done) {
        const { value, done: doneReading } = await reader.read();
        done = doneReading;
        resultText.push(decoder.decode(value, { stream: true }));
      }

      setSimilarDocs(resultText);
      setShowDescription(true);

      setTimeout(() => {
        setShowToast(true);
      }, 7000);

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
      setDroppedImage(null); // Clear the dropped image to prioritize the selected one
      setIsModalOpen(false);
      setShowDescription(false);
    }
  };

  return (
    <div className={styles.content}>
      <div className={styles.imageDescriptorSection}>
        <UserCard name="Luca Napoli" role="Leafy Insurance Customer" image="/assets/eddie.png" />

        <h2>Image Search</h2>

        <div className={styles.dragBox} onDragOver={handleDragOver} onDrop={handleDrop}>
          {imagePreview ? (
            <img className={styles.droppedImage} src={imagePreview} alt="Selected" />
          ) : (
            <p className={styles.dragText}>Drag & Drop your image here</p>
          )}
        </div>

        <Button className={styles.uploadBtn} variant="primary" onClick={handleUpload} disabled={loading}>
          {loading ? <div className={styles.spinner}></div> : "Upload and Generate Description"}
        </Button>

        <p className={styles.link} onClick={() => setIsModalOpen(true)}>
          Choose from sample images
        </p>

        {showDescription && (
          <div className={styles.imageDescription}>
            <Icon className={styles.checkIcon} glyph="Sparkle" />
            <Subtitle className={styles.subtitle}>AI generated image description</Subtitle>
            <div className={styles.similarDocsContainer}>
              {similarDocs.map((doc, index) => (
                <Body key={index} className={styles.similarDoc}>{doc}</Body>
              ))}
            </div>
          </div>
        )}

        <ToastNotification></ToastNotification>
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
        <Button variant="primary" onClick={handleConfirmSelection} className={styles.confirmButtonContainer}>
          Confirm Selection
        </Button>
      </Modal>

      <div className={styles.similarImageSection}>
        <UserCard name="Mark Scout" role="Claim Adjuster" image="/assets/rob.png" />

        <div className={styles.claimContainer}>
          <div className={styles.claimHeader}>
            <Icon className={styles.checkIcon} glyph="Checkmark" />

            <Body>Claim assigned to: <strong>Mark Scout</strong></Body>
          </div>

          <div className={styles.claimDetails}>
            <div className={styles.detailRow}>
              <Body className={styles.detailTitle}>Date created</Body>
              <Body>{new Date().toLocaleDateString()}</Body>
            </div>
            <div className={styles.detailRow}>
              <Body className={styles.detailTitle}>Submitted By</Body>
              <Body>Luca Napoli</Body>

            </div>
            <div className={styles.detailRow}>
              <Body className={styles.detailTitle}>Status</Body>
              <Badge variant="yellow">IN PROGRESS</Badge>
            </div>
          </div>

          <div className={styles.claimSummary}>
            <Subtitle>Accident Summary</Subtitle>
            <Body>{claimDetails ? claimDetails.summary : "..."}</Body>
          </div>

          {/**
          <div className={styles.policySection}>
            <Subtitle>Relevant Policy</Subtitle>
            <div className={styles.policyBox}>Collision with school bus...</div>
          </div>
           */}

          <div className={styles.recommendations}>
            <Subtitle>Recommended next steps</Subtitle>
            <ol>
              <li><Body>Check coverage for medical expenses of any passengers, including those in the passenger vehicle.</Body></li>
              <li><Body>Property damage coverage for the school bus and the other vehicle involved.</Body></li>
            </ol>
          </div>
        </div>
      </div>

    </div>
  );
};

export default ImageDescriptor;
