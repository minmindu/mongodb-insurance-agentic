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
import ToastNotificationRight from "../toastNotificationRight/ToastNotificationRight";

const ImageDescriptor = () => {
  const [droppedImage, setDroppedImage] = useState(null);
  const [imagePreview, setImagePreview] = useState(null);
  const [imageDescription, setImageDescription] = useState("");
  const [loading, setLoading] = useState(false);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [selectedImage, setSelectedImage] = useState(null);
  const [sampleImages, setSampleImages] = useState([]);
  const [showDescription, setShowDescription] = useState(false);
  const [showToast, setShowToast] = useState(false);
  const [claimDetails, setClaimDetails] = useState(null);
  const [showSimilarImageSection, setShowSimilarImageSection] = useState(false);
  const [uploadStatus, setUploadStatus] = useState("idle"); // "idle" | "sending" | "uploaded"
  //const [showToastRight, setShowToastRight] = useState(false);

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
    setUploadStatus("sending"); // Show "SENDING" badge
    setImageDescription(""); // Clear previous description
    setShowDescription(true); // Show description area immediately
    setShowToast(false);
   // setShowToastRight(false);
    setShowSimilarImageSection(false);

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

      while (!done) {
        const { value, done: doneReading } = await reader.read();
        done = doneReading;

        if (value) {
          const chunk = decoder.decode(value, { stream: true });
          console.log("Received chunk:", chunk);

          // Update description directly for the streaming effect
          setImageDescription((prev) => prev + chunk);
        }
      }

      setUploadStatus("uploaded"); // Switch to "UPLOADED FOR REVIEW" badge

      // Show toast notification first
      setTimeout(() => {
        setShowToast(true);
      }, 4000);

      // After description is complete, call the agent
      await runAgent();

    } catch (error) {
      console.error("Error while streaming response:", error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (claimDetails) {
      setShowSimilarImageSection(true);
    }
  }, [claimDetails]);

  const runAgent = async () => {
    try {
      const response = await fetch(process.env.NEXT_PUBLIC_RUN_AGENT_API_URL, {
        method: "POST",
        headers: {
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        throw new Error(`Server error: ${response.status}`);
      }

      const result = await response.json();
      console.log("Agent result recommendation:", result.recommendation);

      // The backend now sends the proper nested structure
      const processedRecommendations = result.recommendation || {
        immediate_actions: [],
        short_term_actions: [],
        approval_guidance: {},
        reserve_recommendations: {}
      };

      // Process priority - convert number to string
      let priorityString = "Standard";
      if (result.priority) {
        if (typeof result.priority === 'number') {
          const priorityMap = {1: "Low", 2: "Medium", 3: "High", 4: "Critical"};
          priorityString = priorityMap[result.priority] || "Standard";
        } else {
          priorityString = String(result.priority);
        }
      }

      setClaimDetails({
        description: result.description || "No summary available",
        recommendation: processedRecommendations,
        approvalLevel: result.approval_level || "Unknown",
        estimatedReserves: result.estimated_reserves || "TBD",
        priority: priorityString,
        timeline: result.timeline || "Standard processing",
        claimHandler: result.claim_handler || "Not assigned"
      });

    } catch (error) {
      console.error("Error calling agent:", error);
    }
  };



  const handleImageSelect = (image) => setSelectedImage(image);

  const handleConfirmSelection = () => {
    if (selectedImage) {
      setImagePreview(selectedImage);
      setDroppedImage(null); // Clear the dropped image to prioritize the selected one
      setIsModalOpen(false);
      setShowDescription(false);
      setImageDescription(""); // Clear previous description
    }
  };

  return (
    <div className={styles.content}>
      <div className={styles.imageDescriptorSection}>
        <UserCard name="Luca Napoli" role="Leafy Insurance Customer" image="/assets/eddie.png" />

        <h2>Upload your claim</h2>

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

            <div className={styles.claimStatusContainer}>
              <Body className={styles.detailTitle}>Claim Status</Body>
              {uploadStatus === "sending" && <Badge variant="yellow">SENDING</Badge>}
              {uploadStatus === "uploaded" && <Badge variant="blue">UPLOADED FOR REVIEW</Badge>}
            </div>

            <div className={styles.imageDescriptionTitle}>
              <Icon className={styles.sparkleIcon} glyph="Sparkle" />
              <Subtitle className={styles.subtitle}>AI generated image description</Subtitle>
            </div>

            <div className={styles.similarDocsContainer}>
              <Body className={styles.similarDoc}>
                {imageDescription || (loading ? "Generating description..." : "")}
              </Body>
            </div>
          </div>
        )}

        {showToast && <ToastNotification text="Your claim is under review and will be assigned shortly" />}

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

      {/**
      {showToastRight && <ToastNotificationRight text="Incoming claim being processed by agent" />}
 */}
      {showSimilarImageSection && (
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
                <Body className={styles.detailTitle}>Claim Handler</Body>
                <Body>{claimDetails ? claimDetails.claimHandler : "Not assigned"}</Body>
              </div>
              <div className={styles.detailRow}>
                <Body className={styles.detailTitle}>Priority Level</Body>
                <Badge variant={
                  claimDetails?.priority?.toLowerCase() === "critical" || claimDetails?.priority?.toLowerCase() === "high" ? "red" : 
                  claimDetails?.priority?.toLowerCase() === "medium" ? "yellow" : 
                  "blue"
                }>
                  {claimDetails?.priority ? String(claimDetails.priority).toUpperCase() : "STANDARD"}
                </Badge>
              </div>
              <div className={styles.detailRow}>
                <Body className={styles.detailTitle}>Approval Required</Body>
                <Body>{claimDetails ? claimDetails.approvalLevel : "TBD"}</Body>
              </div>
              <div className={styles.detailRow}>
                <Body className={styles.detailTitle}>Estimated Reserves</Body>
                <Body>{claimDetails ? claimDetails.estimatedReserves : "TBD"}</Body>
              </div>
              <div className={styles.detailRow}>
                <Body className={styles.detailTitle}>Expected Timeline</Body>
                <Body>{claimDetails ? claimDetails.timeline : "Standard processing"}</Body>
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
              <Body>{claimDetails ? claimDetails.description : "..."}</Body>
            </div>

            <div className={styles.recommendations}>
              <Subtitle>Claim Processing Recommendations</Subtitle>
              
              {/* Immediate Actions Section */}
              {claimDetails?.recommendation?.immediate_actions?.length > 0 && (
                <div className={styles.actionSection}>
                  <Body className={styles.actionHeader}>🚨 IMMEDIATE ACTIONS (Next 4 Hours)</Body>
                  <ol className={styles.actionList}>
                    {claimDetails.recommendation.immediate_actions.map((action, index) => (
                      <li key={index} className={styles.immediateAction}>
                        <Body>{action}</Body>
                      </li>
                    ))}
                  </ol>
                </div>
              )}

              {/* Short-term Actions Section */}
              {claimDetails?.recommendation?.short_term_actions?.length > 0 && (
                <div className={styles.actionSection}>
                  <Body className={styles.actionHeader}>📋 SHORT-TERM ACTIONS (24-72 Hours)</Body>
                  <ol className={styles.actionList}>
                    {claimDetails.recommendation.short_term_actions.map((action, index) => (
                      <li key={index} className={styles.shortTermAction}>
                        <Body>{action}</Body>
                      </li>
                    ))}
                  </ol>
                </div>
              )}

              {/* Approval Guidance Section */}
              {claimDetails?.recommendation?.approval_guidance && 
               Object.keys(claimDetails.recommendation.approval_guidance).length > 0 && 
               (claimDetails.recommendation.approval_guidance.initial_reserve_threshold || 
                claimDetails.recommendation.approval_guidance.supplement_estimate_threshold) && (
                <div className={styles.guidanceSection}>
                  <Body className={styles.actionHeader}>✅ APPROVAL GUIDANCE</Body>
                  <div className={styles.guidanceGrid}>
                    {claimDetails.recommendation.approval_guidance.initial_reserve_threshold && (
                      <div className={styles.guidanceItem}>
                        <Body className={styles.guidanceLabel}>Initial Reserve Threshold:</Body>
                        <Body className={styles.guidanceValue}>${claimDetails.recommendation.approval_guidance.initial_reserve_threshold.toLocaleString()}</Body>
                      </div>
                    )}
                    {claimDetails.recommendation.approval_guidance.supplement_estimate_threshold && (
                      <div className={styles.guidanceItem}>
                        <Body className={styles.guidanceLabel}>Supplement Threshold:</Body>
                        <Body className={styles.guidanceValue}>${claimDetails.recommendation.approval_guidance.supplement_estimate_threshold.toLocaleString()}</Body>
                      </div>
                    )}
                  </div>
                </div>
              )}

              {/* Reserve Recommendations Section */}
              {claimDetails?.recommendation?.reserve_recommendations && 
               Object.keys(claimDetails.recommendation.reserve_recommendations).length > 0 && 
               (claimDetails.recommendation.reserve_recommendations.initial_reserve || 
                claimDetails.recommendation.reserve_recommendations.maximum_reserve) && (
                <div className={styles.reserveSection}>
                  <Body className={styles.actionHeader}>💰 RESERVE RECOMMENDATIONS</Body>
                  <div className={styles.reserveGrid}>
                    {claimDetails.recommendation.reserve_recommendations.initial_reserve && (
                      <div className={styles.reserveItem}>
                        <Body className={styles.reserveLabel}>Initial Reserve:</Body>
                        <Body className={styles.reserveValue}>${claimDetails.recommendation.reserve_recommendations.initial_reserve.toLocaleString()}</Body>
                      </div>
                    )}
                    {claimDetails.recommendation.reserve_recommendations.maximum_reserve && (
                      <div className={styles.reserveItem}>
                        <Body className={styles.reserveLabel}>Maximum Reserve:</Body>
                        <Body className={styles.reserveValue}>${claimDetails.recommendation.reserve_recommendations.maximum_reserve.toLocaleString()}</Body>
                      </div>
                    )}
                  </div>
                </div>
              )}              {/* Decision Tree Section */}
              {claimDetails?.recommendation?.decision_tree && (
                <div className={styles.decisionSection}>
                  <Body className={styles.actionHeader}>🎯 DECISION MATRIX</Body>
                  <div className={styles.decisionGrid}>
                    {claimDetails.recommendation.decision_tree.priority && (
                      <div className={styles.decisionItem}>
                        <Body className={styles.decisionLabel}>Claim Priority:</Body>
                        <Badge variant={claimDetails.recommendation.decision_tree.priority >= 3 ? "red" : claimDetails.recommendation.decision_tree.priority === 2 ? "yellow" : "blue"}>
                          LEVEL {claimDetails.recommendation.decision_tree.priority}
                        </Badge>
                      </div>
                    )}
                    {claimDetails.recommendation.decision_tree.timeline && (
                      <div className={styles.decisionItem}>
                        <Body className={styles.decisionLabel}>Expected Timeline:</Body>
                        <Body className={styles.decisionValue}>{claimDetails.recommendation.decision_tree.timeline}</Body>
                      </div>
                    )}
                  </div>
                </div>
              )}

              {/* Fallback for processed recommendations array */}
              {(!claimDetails?.recommendation?.immediate_actions && 
                !claimDetails?.recommendation?.short_term_actions && 
                claimDetails?.recommendation?.length > 0) && (
                <div className={styles.actionSection}>
                  <Body className={styles.actionHeader}>📋 RECOMMENDATIONS</Body>
                  <ol className={styles.actionList}>
                    {claimDetails.recommendation.map((step, index) => (
                      <li key={index}>
                        <Body>{step}</Body>
                      </li>
                    ))}
                  </ol>
                </div>
              )}

              {/* No recommendations fallback */}
              {(!claimDetails?.recommendation || 
                (Array.isArray(claimDetails.recommendation) && claimDetails.recommendation.length === 0) ||
                (typeof claimDetails.recommendation === 'object' && 
                 !claimDetails.recommendation.immediate_actions && 
                 !claimDetails.recommendation.short_term_actions)) && (
                <Body>No specific recommendations available.</Body>
              )}
            </div>

          </div>
        </div>
      )}
    </div>
  );
};

export default ImageDescriptor;
