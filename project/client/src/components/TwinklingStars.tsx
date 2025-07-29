import { useEffect } from "react";

// Background Twinkling Stars Effect
const TwinklingStars = () => {
  useEffect(() => {
    const container = document.createElement("div");
    container.className = "twinkling-stars";
    document.body.appendChild(container);

    for (let i = 0; i < 40; i++) {
      const star = document.createElement("div");
      star.className = "star";
      star.style.top = `${Math.random() * 100}vh`;
      star.style.left = `${Math.random() * 100}vw`;
      star.style.animationDelay = `${Math.random() * 5}s`;
      container.appendChild(star);
    }

    return () => container.remove(); // Clean up on unmount
  }, []);

  return null;
};

export { TwinklingStars };
