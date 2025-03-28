import { useState, useEffect } from "react";
import styles from "./toastNotification.module.css";

const ToastNotification = () => {
  const [visible, setVisible] = useState(true);

  useEffect(() => {
    const timer = setTimeout(() => {
      setVisible(false);
    }, 5000); // Auto-hide after 5 seconds

    return () => clearTimeout(timer);
  }, []);

  if (!visible) return null;

  return (
    <div className={styles.toast}>
      Your claim is under review and will be assigned shortly
    </div>
  );
};

export default ToastNotification;
