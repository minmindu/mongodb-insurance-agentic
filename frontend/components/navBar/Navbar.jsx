"use client";

import UserProfile from "../userProfile/UserProfile";
import styles from "./navbar.module.css";
import Image from "next/image";
import { useState } from "react";
import InfoWizard from "../InfoWizard/InfoWizard";

const Navbar = () => {
  const [openHelpModal, setOpenHelpModal] = useState(false);
  return (
    <nav className={styles.navbar}>
      <div className={styles.logo}>
        <Image src="/assets/logo.png" alt="Logo" width={200} height={40} />{" "}
      </div>
      <InfoWizard
        open={openHelpModal}
        setOpen={setOpenHelpModal}
        tooltipText="Tell me more!"
        iconGlyph="Wizard"

        sections={[
          {
            heading: "Instructions and Talk Track",
            content: [
              {
                heading: "Agentic AI in Insurance",
                body: "...",
              },
              {
                heading: "How to Demo",
                body: [
                  "Drag and drop an image into the box or select one from the sample images.",
                  "Press 'Upload and Generate Description'.",
                  "..."
                ],
              },
            ],
          },
          {
            heading: "Behind the Scenes",
            content: [
              {
                heading: "Data Flow",
                body: "This section explains how data moves through the system, from ingestion to query execution.",
                images: [
                  {
                    src: "assets/ingest.png",
                    alt: "Ingest Architecture",
                  },
                  {
                    src: "assets/query.png",
                    alt: "Query Architecture",
                  },
                ],
              },
            ],
          },
          {
            heading: "Why MongoDB?",
            content: [
              {
                heading: "Operational and Vector Database Combined",
                body: "MongoDB stores vectors alongside operational data, eliminating the need to having two separate solutions. Enabling features such as pre-filtering.",

              },
              {
                heading: "Performance",
                body: "MongoDB's Vector Search is extremely fast at retrieving vectors.",

              },
            ],
          },
        ]}
      />
      {/*<div className={styles.user}>
        <UserProfile />
      </div>
      */}
    </nav>
  );
};

export default Navbar;
