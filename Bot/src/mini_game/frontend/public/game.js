// Enhanced Shabbat Runner with Rabbi guide - Complete JavaScript implementation

/**
 * Draws a dynamic parallax background with sunset gradient and moving city silhouettes
 * Creates an atmospheric Shabbat evening scene with twinkling stars and warm lights
 * @param {CanvasRenderingContext2D} ctx - The canvas rendering context
 * @param {number} width - Canvas width in pixels
 * @param {number} height - Canvas height in pixels
 * @param {number} time - Current game time for animation timing
 */
function drawParallaxBackground(ctx, width, height, time) {
  // Sunset gradient background
  const sunsetGradient = ctx.createLinearGradient(0, 0, 0, height);
  sunsetGradient.addColorStop(0, '#FF6B47'); // Warm orange top
  sunsetGradient.addColorStop(0.3, '#FF8566'); // Orange
  sunsetGradient.addColorStop(0.6, '#9D4EDD'); // Purple
  sunsetGradient.addColorStop(0.8, '#3C096C'); // Deep purple
  sunsetGradient.addColorStop(1, '#10002B'); // Dark bottom
  
  ctx.fillStyle = sunsetGradient;
  ctx.fillRect(0, 0, width, height);
  
  // Parallax city silhouettes (moving slowly)
  const cityOffset = (time * 0.02) % width;
  
  // Background buildings layer
  ctx.fillStyle = '#1A0033';
  for (let i = 0; i < 8; i++) {
    const x = (i * 80 - cityOffset * 0.3) % (width + 80);
    const buildingHeight = 60 + Math.sin(i) * 20;
    ctx.fillRect(x, height - buildingHeight, 60, buildingHeight);
    
    // Windows (golden Shabbat lights)
    ctx.fillStyle = '#FFD700';
    for (let w = 0; w < 3; w++) {
      for (let h = 0; h < 4; h++) {
        if (Math.random() > 0.3) {
          ctx.fillRect(x + 10 + w * 15, height - buildingHeight + 10 + h * 12, 8, 8);
        }
      }
    }
    ctx.fillStyle = '#1A0033';
  }
  
  // Foreground houses layer
  ctx.fillStyle = '#0D0022';
  for (let i = 0; i < 6; i++) {
    const x = (i * 120 - cityOffset) % (width + 120);
    const houseHeight = 80 + Math.cos(i) * 15;
    ctx.fillRect(x, height - houseHeight, 100, houseHeight);
    
    // Rooftops
    ctx.fillStyle = '#2A0040';
    ctx.fillRect(x - 10, height - houseHeight, 120, 15);
    
    // Warm house lights
    ctx.fillStyle = '#FFA500';
    ctx.fillRect(x + 20, height - houseHeight + 20, 12, 12);
    ctx.fillRect(x + 60, height - houseHeight + 30, 12, 12);
    
    ctx.fillStyle = '#0D0022';
  }
  
  // Twinkling stars
  ctx.fillStyle = '#FFFFFF';
  for (let i = 0; i < 30; i++) {
    const starX = (i * 67) % width;
    const starY = (i * 43) % (height * 0.4);
    const twinkle = Math.sin(time * 0.005 + i) > 0.8;
    if (twinkle) {
      ctx.fillRect(starX, starY, 2, 2);
    }
  }
}

/**
 * Renders game items with dynamic glow effects and click animations
 * Holy items get golden pulsing glow, forbidden items get red flickering
 * Includes scale and rotation animations for user feedback
 * @param {CanvasRenderingContext2D} ctx - The canvas rendering context
 * @param {Object} obj - Game object with properties: x, y, size, isGood, scaleAnimation
 * @param {number} time - Current game time for animation timing
 */
function drawItemWithGlow(ctx, obj, time) {
  const centerX = obj.x + obj.size / 2;
  const centerY = obj.y + obj.size / 2;
  
  // Handle click scale animation
  let currentScale = 1.0;
  let currentRotation = 0;
  
  if (obj.scaleAnimation) {
    const progress = 1 - (obj.scaleAnimation.timer / 200);
    
    if (obj.scaleAnimation.direction === 1) {
      // Positive click: 1.0 → 1.2 → 1.0
      if (progress < 0.5) {
        currentScale = 1.0 + (progress * 2) * 0.2; // 1.0 to 1.2
      } else {
        currentScale = 1.2 - ((progress - 0.5) * 2) * 0.2; // 1.2 to 1.0
      }
    } else {
      // Negative click: 1.0 → 0.8 → 1.0 with shake
      if (progress < 0.5) {
        currentScale = 1.0 - (progress * 2) * 0.2; // 1.0 to 0.8
        currentRotation = (Math.random() - 0.5) * 0.2; // shake
      } else {
        currentScale = 0.8 + ((progress - 0.5) * 2) * 0.2; // 0.8 to 1.0
        currentRotation = (Math.random() - 0.5) * 0.1; // less shake
      }
    }
    
    obj.scaleAnimation.timer -= 16; // Assuming 60fps
    if (obj.scaleAnimation.timer <= 0) {
      obj.scaleAnimation = null;
    }
  }
  
  if (obj.isGood) {
    // Golden pulsing glow for holy items
    const glowIntensity = 0.7 + 0.3 * Math.sin(time * 0.008);
    const glowSize = obj.size * (1.2 + glowIntensity * 0.3) * currentScale;
    
    const goldenGlow = ctx.createRadialGradient(centerX, centerY, 0, centerX, centerY, glowSize);
    goldenGlow.addColorStop(0, `rgba(255, 215, 0, ${glowIntensity * 0.4})`);
    goldenGlow.addColorStop(0.7, `rgba(255, 165, 0, ${glowIntensity * 0.2})`);
    goldenGlow.addColorStop(1, 'rgba(255, 215, 0, 0)');
    
    ctx.fillStyle = goldenGlow;
    ctx.fillRect(centerX - glowSize, centerY - glowSize, glowSize * 2, glowSize * 2);
  } else {
    // Cold red/blue flicker for forbidden items
    const flickerR = Math.random() > 0.5 ? 255 : 100;
    const flickerB = Math.random() > 0.5 ? 255 : 150;
    const flickerIntensity = 0.5 + 0.5 * Math.random();
    
    const forbiddenGlow = ctx.createRadialGradient(centerX, centerY, 0, centerX, centerY, obj.size * 1.3 * currentScale);
    forbiddenGlow.addColorStop(0, `rgba(${flickerR}, 50, ${flickerB}, ${flickerIntensity * 0.3})`);
    forbiddenGlow.addColorStop(0.8, `rgba(${flickerR}, 30, ${flickerB}, ${flickerIntensity * 0.1})`);
    forbiddenGlow.addColorStop(1, 'rgba(255, 0, 0, 0)');
    
    ctx.fillStyle = forbiddenGlow;
    const glowRadius = obj.size * currentScale;
    ctx.fillRect(centerX - glowRadius, centerY - glowRadius, glowRadius * 2, glowRadius * 2);
  }
  
  // Draw the emoji with scale and rotation
  ctx.save();
  ctx.translate(centerX, centerY);
  ctx.rotate(currentRotation);
  ctx.scale(currentScale, currentScale);
  
  ctx.font = `${obj.size}px Arial`;
  ctx.textAlign = 'center';
  ctx.textBaseline = 'middle';
  ctx.fillStyle = '#FFFFFF';
  ctx.strokeStyle = '#000000';
  ctx.lineWidth = 2;
  ctx.strokeText(obj.emoji, 0, 0);
  ctx.fillText(obj.emoji, 0, 0);
  
  ctx.restore();
}

// Internationalization system with humorous Rabbi lines
const rabbiLines = {
  english: {
    start: [
      "Run, run! The challah is getting cold!",
      "Shabbat won't wait for Wi-Fi!",
      "Quick! The candles are waiting to be lit!",
      "Hurry! Your grandmother's soup is ready!"
    ],
    good: [
      "Kedusha +1",
      "Shabbat shalom!",
      "Mazal tov!",
      "Beautiful mitzvah!",
      "Holy sparks!"
    ],
    bad: [
      "Not on Shabbat!",
      "Oy vey! Put it away!",
      "Shabbat rest, tech rest!",
      "Sacred time, my friend!",
      "Choose kedusha instead!"
    ],
    end: [
      "Mazal tov! Shabbat shalom!",
      "You collected {score} holy sparks!",
      "Beautiful! Your soul shines bright!",
      "Wonderful job! The angels are singing!",
      "Perfect! Your Shabbat table is blessed!"
    ]
  },
  russian: {
    start: [
      "Беги, беги! Хала остывает!",
      "Шаббат не ждёт Wi-Fi!",
      "Быстрее! Свечи ждут зажжения!",
      "Торопись! Суп бабушки готов!"
    ],
    good: [
      "Кдуша +1",
      "Шаббат шалом!",
      "Мазаль тов!",
      "Прекрасная мицва!",
      "Святые искры!"
    ],
    bad: [
      "Не в Шаббат!",
      "Ой-вей! Убери это!",
      "Шаббат отдых, техника отдых!",
      "Священное время, друг!",
      "Выбери кдушу!"
    ],
    end: [
      "Мазаль тов! Шаббат шалом!",
      "Ты собрал {score} святых искр!",
      "Прекрасно! Твоя душа сияет!",
      "Отличная работа! Ангелы поют!",
      "Идеально! Твой стол Шаббата благословен!"
    ]
  },
  hebrew: {
    start: [
      "רוץ, רוץ! החלה מתקררת!",
      "שבת לא מחכה לאינטרנט!",
      "מהר! הנרות מחכים להדלקה!",
      "מהר! המרק של סבתא מוכן!"
    ],
    good: [
      "קדושה +1",
      "שבת שלום!",
      "מזל טוב!",
      "מצווה יפה!",
      "ניצוצות קדושה!"
    ],
    bad: [
      "לא בשבת!",
      "אוי ואבוי! תסיר זה!",
      "שבת מנוחה, טכנולוגיה מנוחה!",
      "זמן קדוש, ידידי!",
      "בחר בקדושה!"
    ],
    end: [
      "מזל טוב! שבת שלום!",
      "אספת {score} ניצוצות קדושה!",
      "נפלא! הנשמה שלך זוהרת!",
      "עבודה נפלאה! המלאכים שרים!",
      "מושלם! שולחן השבת שלך מבורך!"
    ]
  }
};

/**
 * Retrieves a random text line from the Rabbi's speech library
 * Supports multiple languages with English as fallback
 * @param {string} category - Text category: 'start', 'good', 'bad', or 'end'
 * @param {string} [language='english'] - Language code (english, russian, hebrew)
 * @returns {string} Random text line from the specified category
 */
function getRandomLine(category, language = 'english') {
  const lines = rabbiLines[language]?.[category] || rabbiLines.english[category];
  return lines[Math.floor(Math.random() * lines.length)];
}

/**
 * Formats the game end message with the player's score
 * Uses template replacement to insert score into localized messages
 * @param {number} score - The player's final score
 * @param {string} [language='english'] - Language for the message
 * @returns {string} Formatted end game message with score
 */
function formatEndMessage(score, language = 'english') {
  const template = getRandomLine('end', language);
  return template.replace('{score}', score.toString());
}

/**
 * Rabbi mascot system - provides visual guidance and multilingual feedback
 * Displays a pixel-art rabbi character with speech bubbles for player interaction
 * Supports multiple languages and emotional responses to game events
 */
class Rabbi {
  constructor(gameCanvas) {
    this.ctx = gameCanvas.getContext('2d');
    
    // Create speech bubble overlay (positioned below HUD to avoid overlap)
    this.speechDiv = document.createElement('div');
    this.speechDiv.style.cssText = `
      position: absolute;
      top: 120px;
      left: 50%;
      transform: translateX(-50%);
      max-width: 280px;
      background: rgba(255, 255, 255, 0.95);
      border: 3px solid #4A90E2;
      border-radius: 16px;
      padding: 12px;
      font-family: Inter, sans-serif;
      font-size: 15px;
      font-weight: 600;
      color: #2C3E50;
      opacity: 0;
      pointer-events: none;
      z-index: 20;
      transition: opacity 0.3s ease;
      box-shadow: 0 6px 16px rgba(0,0,0,0.2);
      transform: translateY(-10px);
    `;
    gameCanvas.parentElement.appendChild(this.speechDiv);
    
    this.state = {
      x: 20,
      y: 100,
      speechVisible: false,
      speechTimer: 0
    };
  }

  update(deltaTime) {
    if (this.state.speechVisible) {
      this.state.speechTimer -= deltaTime;
      if (this.state.speechTimer <= 0) {
        this.hideSpeech();
      }
    }
  }

  render() {
    const { x, y } = this.state;
    
    // Disable antialiasing for pixel-perfect 8-bit style
    this.ctx.imageSmoothingEnabled = false;
    
    // PIXAR + 8-bit Rabbi inspired by rabbi_welcome.png
    // Round head base (PIXAR style with pixels)
    this.ctx.fillStyle = '#FFCC99';
    this.ctx.fillRect(x + 15, y + 8, 30, 22);
    this.ctx.fillRect(x + 12, y + 12, 36, 14);
    this.ctx.fillRect(x + 10, y + 16, 40, 8);
    
    // Black kippah (detailed pixelated)
    this.ctx.fillStyle = '#1a1a1a';
    this.ctx.fillRect(x + 18, y + 2, 24, 8);
    this.ctx.fillRect(x + 16, y + 6, 28, 6);
    this.ctx.fillRect(x + 14, y + 8, 32, 4);
    
    // Large round glasses (PIXAR characteristic)
    this.ctx.fillStyle = '#333333';
    // Left lens frame
    this.ctx.fillRect(x + 16, y + 14, 10, 8);
    this.ctx.fillRect(x + 14, y + 16, 14, 4);
    // Right lens frame
    this.ctx.fillRect(x + 34, y + 14, 10, 8);
    this.ctx.fillRect(x + 32, y + 16, 14, 4);
    // Bridge
    this.ctx.fillRect(x + 26, y + 16, 8, 3);
    
    // Glass lenses (clear/white)
    this.ctx.fillStyle = '#f8f8f8';
    this.ctx.fillRect(x + 17, y + 15, 8, 6);
    this.ctx.fillRect(x + 35, y + 15, 8, 6);
    
    // Large expressive eyes (PIXAR style)
    this.ctx.fillStyle = '#000000';
    this.ctx.fillRect(x + 19, y + 17, 4, 3);
    this.ctx.fillRect(x + 37, y + 17, 4, 3);
    // Eye highlights
    this.ctx.fillStyle = '#FFFFFF';
    this.ctx.fillRect(x + 20, y + 17, 2, 1);
    this.ctx.fillRect(x + 38, y + 17, 2, 1);
    
    // Warm nose (PIXAR rounded style)
    this.ctx.fillStyle = '#FFB366';
    this.ctx.fillRect(x + 28, y + 20, 4, 3);
    this.ctx.fillRect(x + 27, y + 21, 6, 2);
    
    // Fluffy white beard (PIXAR volume + 8-bit)
    this.ctx.fillStyle = '#FFFFFF';
    this.ctx.fillRect(x + 14, y + 24, 32, 16);
    this.ctx.fillRect(x + 12, y + 28, 36, 12);
    this.ctx.fillRect(x + 10, y + 32, 40, 10);
    this.ctx.fillRect(x + 8, y + 36, 44, 8);
    
    // Beard texture and volume (PIXAR style curls)
    this.ctx.fillStyle = '#F5F5F5';
    this.ctx.fillRect(x + 16, y + 26, 4, 4);
    this.ctx.fillRect(x + 30, y + 30, 4, 4);
    this.ctx.fillRect(x + 22, y + 34, 4, 4);
    this.ctx.fillRect(x + 38, y + 38, 4, 4);
    this.ctx.fillRect(x + 14, y + 40, 4, 4);
    
    // Warm brown robe (earth tones)
    this.ctx.fillStyle = '#8B4513';
    this.ctx.fillRect(x + 6, y + 44, 48, 24);
    this.ctx.fillRect(x + 4, y + 50, 52, 18);
    
    // Robe shadows and depth (PIXAR lighting)
    this.ctx.fillStyle = '#654321';
    this.ctx.fillRect(x + 8, y + 46, 4, 20);
    this.ctx.fillRect(x + 44, y + 46, 4, 20);
    this.ctx.fillRect(x + 6, y + 64, 48, 4);
    
    // Sacred Torah book (golden binding)
    this.ctx.fillStyle = '#DAA520';
    this.ctx.fillRect(x + 36, y + 48, 14, 10);
    this.ctx.fillStyle = '#B8860B';
    this.ctx.fillRect(x + 38, y + 50, 10, 6);
    // Hebrew letters on book
    this.ctx.fillStyle = '#000000';
    this.ctx.fillRect(x + 39, y + 51, 2, 1);
    this.ctx.fillRect(x + 42, y + 52, 2, 1);
    this.ctx.fillRect(x + 45, y + 51, 2, 1);
    this.ctx.fillRect(x + 40, y + 54, 6, 1);
    
    // Gentle hands holding book
    this.ctx.fillStyle = '#FFCC99';
    this.ctx.fillRect(x + 32, y + 50, 6, 4);
    this.ctx.fillRect(x + 48, y + 52, 6, 4);
    
    // No emotion emoji overlay - clean Rabbi avatar
    
    // Re-enable smoothing for other elements
    this.ctx.imageSmoothingEnabled = true;
  }

  /**
   * Displays a speech bubble with the given text
   * @param {string} text - Text to display in the speech bubble
   * @param {number} [duration=2000] - Duration to show the speech in milliseconds
   */
  speak(text, duration = 2000) {
    this.speechDiv.textContent = text;
    this.speechDiv.style.opacity = '1';
    this.state.speechVisible = true;
    this.state.speechTimer = duration;
  }

  hideSpeech() {
    this.speechDiv.style.opacity = '0';
    this.state.speechVisible = false;
  }

  celebrate() {
    // Visual celebration through speech only
  }

  disappointedButKind() {
    // Visual disappointment through speech only  
  }

  excited() {
    // Visual excitement through speech only
  }
}

/**
 * Visual effects system for particle effects, screen shake, and animations
 * Manages holy item sparkles, forbidden item effects, and UI feedback
 * Provides screen shake, floating text, and various particle systems
 */
class FXSystem {
  constructor(canvas) {
    this.ctx = canvas.getContext('2d');
    this.particles = [];
    this.shakeIntensity = 0;
    this.shakeTimer = 0;
    this.clickAnimations = [];
    this.floatingTexts = [];
  }

  update(deltaTime) {
    // Update shake
    if (this.shakeTimer > 0) {
      this.shakeTimer -= deltaTime;
      this.shakeIntensity = Math.max(0, this.shakeIntensity * 0.9);
    }

    // Update particles
    for (let i = this.particles.length - 1; i >= 0; i--) {
      const p = this.particles[i];
      
      if (p.type === 'halo') {
        p.radius = (1 - p.life / p.maxLife) * p.maxRadius;
      } else if (p.type === 'shockwave') {
        p.radius = (1 - p.life / p.maxLife) * p.maxRadius;
      } else if (p.type === 'shard') {
        p.x += p.vx * deltaTime / 16;
        p.y += p.vy * deltaTime / 16;
        p.rotation += p.rotationSpeed * deltaTime / 16;
      } else {
        p.x += p.vx * deltaTime / 16;
        p.y += p.vy * deltaTime / 16;
        p.vy += 0.5; // Gravity
      }
      
      p.life -= deltaTime;

      if (p.life <= 0) {
        this.particles.splice(i, 1);
      }
    }

    // Update floating texts
    for (let i = this.floatingTexts.length - 1; i >= 0; i--) {
      const text = this.floatingTexts[i];
      text.y += text.vy * deltaTime / 16;
      text.life -= deltaTime;

      if (text.life <= 0) {
        this.floatingTexts.splice(i, 1);
      }
    }
  }

  render() {
    // Apply screen shake
    if (this.shakeIntensity > 0) {
      const offsetX = (Math.random() - 0.5) * this.shakeIntensity;
      const offsetY = (Math.random() - 0.5) * this.shakeIntensity;
      this.ctx.save();
      this.ctx.translate(offsetX, offsetY);
    }

    // Render particles
    this.particles.forEach(p => {
      const alpha = p.life / p.maxLife;
      this.ctx.globalAlpha = alpha;

      if (p.type === 'halo') {
        // Golden halo expanding circle
        const gradient = this.ctx.createRadialGradient(p.x, p.y, 0, p.x, p.y, p.radius);
        gradient.addColorStop(0, p.color);
        gradient.addColorStop(1, 'rgba(255, 215, 0, 0)');
        this.ctx.fillStyle = gradient;
        this.ctx.beginPath();
        this.ctx.arc(p.x, p.y, p.radius, 0, Math.PI * 2);
        this.ctx.fill();
      } else if (p.type === 'shockwave') {
        // Red-blue alternating shockwave
        this.ctx.strokeStyle = alpha > 0.5 ? p.color1 : p.color2;
        this.ctx.lineWidth = 3;
        this.ctx.beginPath();
        this.ctx.arc(p.x, p.y, p.radius, 0, Math.PI * 2);
        this.ctx.stroke();
      } else if (p.type === 'flash') {
        // White flash circle
        this.ctx.fillStyle = p.color;
        this.ctx.beginPath();
        this.ctx.arc(p.x, p.y, p.radius, 0, Math.PI * 2);
        this.ctx.fill();
      } else if (p.type === 'shard') {
        // Angular rotating shards
        this.ctx.save();
        this.ctx.translate(p.x, p.y);
        this.ctx.rotate(p.rotation);
        this.ctx.fillStyle = '#FF6666';
        this.ctx.fillRect(-p.size/2, -p.size/2, p.size, p.size);
        this.ctx.restore();
      } else if (p.type === 'spark') {
        // Spark particles (stars)
        this.ctx.font = `${p.size * 3}px Arial`;
        this.ctx.textAlign = 'center';
        this.ctx.fillStyle = '#FFD700';
        this.ctx.fillText(p.emoji, p.x, p.y);
      } else if (p.emoji) {
        // Regular emoji particles
        this.ctx.font = `${p.size}px Arial`;
        this.ctx.textAlign = 'center';
        this.ctx.fillText(p.emoji, p.x, p.y);
      } else {
        // Regular colored particles
        this.ctx.fillStyle = p.color;
        this.ctx.beginPath();
        this.ctx.arc(p.x, p.y, p.size, 0, Math.PI * 2);
        this.ctx.fill();
      }
    });

    // Render floating texts
    this.floatingTexts.forEach(text => {
      const alpha = text.life / text.maxLife;
      this.ctx.globalAlpha = alpha;
      this.ctx.font = '14px "Press Start 2P", monospace';
      this.ctx.textAlign = 'center';
      this.ctx.fillStyle = text.color;
      this.ctx.strokeStyle = '#000000';
      this.ctx.lineWidth = 2;
      
      let renderX = text.x;
      let renderY = text.y;
      
      // Add shake effect for negative texts
      if (text.shake) {
        renderX += (Math.random() - 0.5) * 4;
        renderY += (Math.random() - 0.5) * 2;
      }
      
      this.ctx.strokeText(text.text, renderX, renderY);
      this.ctx.fillText(text.text, renderX, renderY);
    });

    this.ctx.globalAlpha = 1;

    if (this.shakeIntensity > 0) {
      this.ctx.restore();
    }
  }

  // Kedusha Spark - positive click animation
  createKedushaSpark(x, y) {
    // Golden halo burst
    this.particles.push({
      type: 'halo',
      x: x,
      y: y,
      radius: 0,
      maxRadius: 50,
      life: 1000,
      maxLife: 1000,
      color: 'rgba(255, 215, 0, 0.8)'
    });

    // 6-8 spark particles
    for (let i = 0; i < 8; i++) {
      const angle = (i / 8) * Math.PI * 2 + Math.random() * 0.5;
      const speed = 2 + Math.random() * 3;
      this.particles.push({
        type: 'spark',
        x: x,
        y: y,
        vx: Math.cos(angle) * speed,
        vy: Math.sin(angle) * speed,
        life: 800,
        maxLife: 800,
        size: 3 + Math.random() * 2,
        emoji: Math.random() > 0.5 ? '✨' : '⭐'
      });
    }

    // Floating positive text
    this.floatingTexts.push({
      x: x,
      y: y,
      text: Math.random() > 0.5 ? '+1' : 'Kedusha',
      life: 600,
      maxLife: 600,
      color: '#FFD700',
      vy: -1
    });
  }

  // Chill Blast - negative click animation
  createChillBlast(x, y) {
    // Red-blue shockwave
    this.particles.push({
      type: 'shockwave',
      x: x,
      y: y,
      radius: 0,
      maxRadius: 40,
      life: 150,
      maxLife: 150,
      color1: 'rgba(255, 0, 0, 0.6)',
      color2: 'rgba(0, 100, 255, 0.4)'
    });

    // White flash
    this.particles.push({
      type: 'flash',
      x: x,
      y: y,
      radius: 25,
      life: 100,
      maxLife: 100,
      color: 'rgba(255, 255, 255, 0.8)'
    });

    // 5-6 angular shards
    for (let i = 0; i < 6; i++) {
      const angle = (i / 6) * Math.PI * 2 + Math.random() * 0.3;
      const speed = 1.5 + Math.random() * 2;
      this.particles.push({
        type: 'shard',
        x: x,
        y: y,
        vx: Math.cos(angle) * speed,
        vy: Math.sin(angle) * speed,
        life: 500,
        maxLife: 500,
        size: 4 + Math.random() * 3,
        rotation: Math.random() * Math.PI * 2,
        rotationSpeed: (Math.random() - 0.5) * 0.2
      });
    }

    // Floating negative text
    this.floatingTexts.push({
      x: x,
      y: y,
      text: Math.random() > 0.5 ? '-1' : 'Not on Shabbat!',
      life: 500,
      maxLife: 500,
      color: '#FF4444',
      vy: 0.5, // falls down
      shake: true
    });
  }

  createSparkles(x, y) {
    for (let i = 0; i < 8; i++) {
      this.particles.push({
        x: x + (Math.random() - 0.5) * 40,
        y: y + (Math.random() - 0.5) * 40,
        vx: (Math.random() - 0.5) * 4,
        vy: (Math.random() - 0.5) * 4 - 2,
        life: 1000,
        maxLife: 1000,
        color: ['#FFD700', '#FFA500', '#FF69B4', '#00CED1'][Math.floor(Math.random() * 4)],
        size: 3 + Math.random() * 3,
        emoji: ['✨', '⭐', '💫'][Math.floor(Math.random() * 3)]
      });
    }
  }

  createExplosion(x, y) {
    this.shake(10, 300);
    
    for (let i = 0; i < 6; i++) {
      this.particles.push({
        x: x + (Math.random() - 0.5) * 30,
        y: y + (Math.random() - 0.5) * 30,
        vx: (Math.random() - 0.5) * 6,
        vy: (Math.random() - 0.5) * 6 - 3,
        life: 800,
        maxLife: 800,
        color: ['#FF4444', '#CC0000', '#FF6666'][Math.floor(Math.random() * 3)],
        size: 4 + Math.random() * 4,
        emoji: ['💥', '❌', '🚫'][Math.floor(Math.random() * 3)]
      });
    }
  }

  shake(intensity, duration) {
    this.shakeIntensity = intensity;
    this.shakeTimer = duration;
  }

  clear() {
    this.particles = [];
    this.shakeIntensity = 0;
    this.shakeTimer = 0;
  }
}

// Audio system using Web Audio API
class AudioSystem {
  constructor() {
    this.audioContext = null;
    this.enabled = true;
    this.initializeAudio();
  }

  initializeAudio() {
    try {
      this.audioContext = new (window.AudioContext || window.webkitAudioContext)();
    } catch (e) {
      console.warn('Audio not available:', e);
      this.enabled = false;
    }
  }

  createTone(frequency, duration, type = 'sine') {
    if (!this.enabled || !this.audioContext) return;

    try {
      const oscillator = this.audioContext.createOscillator();
      const gainNode = this.audioContext.createGain();
      
      oscillator.connect(gainNode);
      gainNode.connect(this.audioContext.destination);
      
      oscillator.frequency.setValueAtTime(frequency, this.audioContext.currentTime);
      oscillator.type = type;
      
      gainNode.gain.setValueAtTime(0, this.audioContext.currentTime);
      gainNode.gain.linearRampToValueAtTime(0.1, this.audioContext.currentTime + 0.01);
      gainNode.gain.exponentialRampToValueAtTime(0.001, this.audioContext.currentTime + duration);
      
      oscillator.start(this.audioContext.currentTime);
      oscillator.stop(this.audioContext.currentTime + duration);
    } catch (e) {
      console.warn('Audio playback failed:', e);
    }
  }

  playCollectSound() {
    this.createTone(523, 0.2); // C5
    setTimeout(() => this.createTone(659, 0.2), 100); // E5
  }

  playMistakeSound() {
    this.createTone(200, 0.3, 'square');
  }

  playStartSound() {
    this.createTone(440, 0.2); // A4
    setTimeout(() => this.createTone(523, 0.2), 150); // C5
    setTimeout(() => this.createTone(659, 0.3), 300); // E5
  }

  playEndSound() {
    this.createTone(523, 0.2); // C5
    setTimeout(() => this.createTone(659, 0.2), 200); // E5
    setTimeout(() => this.createTone(784, 0.2), 400); // G5
    setTimeout(() => this.createTone(1047, 0.4), 600); // C6
  }
}

// CONSOLIDATED JAVASCRIPT - All code moved from HTML to game.js
        
        // TELEGRAM WEBAPP API INTEGRATION - Системное решение скролла
        
        // Environment Detection
        function isTelegramWebView() {
            return window.Telegram && window.Telegram.WebApp && window.Telegram.WebApp.initData;
        }
        
        // Telegram-specific configuration
        function initializeTelegramEnvironment() {
            if (!isTelegramWebView()) {
                return false;
            }
            
            
            try {
                // Expand to full height
                if (window.Telegram.WebApp.expand) {
                    window.Telegram.WebApp.expand();
                    console.log('✅ WebApp expanded to full screen');
                }
                
                // SELECTIVE: Allow scroll inside content, prevent only app closure swipes
                // We'll use CSS touch-action instead of global disableVerticalSwipes
                console.log('ℹ️ Using selective touch-action control instead of global swipe disable');
                
                // Set header color to match tutorial theme
                if (window.Telegram.WebApp.setHeaderColor) {
                    window.Telegram.WebApp.setHeaderColor('#1a1a2e');
                }
                
                // Ready signal
                window.Telegram.WebApp.ready();
                
                return true;
            } catch (error) {
                console.error('❌ Telegram API initialization failed:', error);
                return false;
            }
        }
        
        // CSS Override for WebView Environment  
        function applyWebViewOptimizations() {
            const style = document.createElement('style');
            style.textContent = `
                /* Telegram WebView Optimizations */
                html, body {
                    overscroll-behavior: none !important;
                    -webkit-overflow-scrolling: touch;
                    overflow-x: hidden;
                    height: 100%;
                }
                
                /* Tutorial card optimizations for WebView */
                .tutorial-card {
                    -webkit-overflow-scrolling: touch;
                    overscroll-behavior: contain;
                    scroll-behavior: smooth;
                }
                
                /* Allow vertical scrolling in overlay, prevent app closure */
                .tutorial-overlay {
                    touch-action: pan-y pinch-zoom;
                    overscroll-behavior: none;
                }
            `;
            document.head.appendChild(style);
            console.log('✅ WebView CSS optimizations applied');
        }
        
        // Fallback strategies for non-Telegram browsers
        function applyFallbackStrategies() {
            if (window.gameEnvironment && window.gameEnvironment.fallbackMode) {
                console.log('🔄 Applying fallback scroll strategies for non-Telegram environment');
                
                // Prevent document overscroll that could interfere
                document.body.style.overscrollBehavior = 'none';
                
                // Ensure document is scrollable (prevents iOS Safari issues)
                const ensureScrollable = () => {
                    const isScrollable = document.documentElement.scrollHeight > window.innerHeight;
                    if (!isScrollable) {
                        document.documentElement.style.setProperty("height", "calc(100vh + 1px)", "important");
                    }
                };
                
                ensureScrollable();
                window.addEventListener('resize', ensureScrollable);
                
                // Monitor scroll to prevent unwanted behavior
                let lastScrollTop = 0;
                window.addEventListener('scroll', () => {
                    const scrollTop = window.pageYOffset || document.documentElement.scrollTop;
                    if (scrollTop > lastScrollTop && scrollTop > 0) {
                        // Scrolling down - prevent collapse by resetting
                        if (scrollTop < 50) window.scrollTo(0, 0);
                    }
                    lastScrollTop = scrollTop;
                });
                
                console.log('✅ Fallback strategies applied');
            }
        }
        
        // SCROLL DIAGNOSTICS - Simplified for production
        
        function initScrollDiagnostics() {
            // Simplified scroll monitoring for production
            let touchEventCounter = 0;
            
            // Touch event tracking (minimal logging)
            ['touchstart', 'touchmove', 'touchend', 'touchcancel'].forEach(eventType => {
                document.addEventListener(eventType, function(e) {
                    touchEventCounter++;
                }, { passive: true });
            });
            
            // Monitor tutorial card scroll events specifically
            document.addEventListener('scroll', function(e) {
                if (e.target.classList && e.target.classList.contains('tutorial-card')) {
                    console.log('📜 TUTORIAL SCROLL EVENT:', {
                        scrollTop: e.target.scrollTop,
                        scrollHeight: e.target.scrollHeight,
                        clientHeight: e.target.clientHeight,
                        canScroll: e.target.scrollHeight > e.target.clientHeight
                    });
                }
            }, true);
            
            // Content size monitoring for tutorial cards
            function measureTutorialContent() {
                const tutorialCards = document.querySelectorAll('.tutorial-card');
                tutorialCards.forEach((card, index) => {
                    const content = card.querySelector('.tutorial-content');
                    if (card.offsetParent !== null) { // только для видимых
                        console.log(`📏 TUTORIAL CARD ${index + 1} SIZES:`, {
                            cardHeight: card.clientHeight,
                            cardScrollHeight: card.scrollHeight,
                            contentHeight: content ? content.scrollHeight : 'N/A',
                            canScroll: card.scrollHeight > card.clientHeight,
                            isOverflowing: card.scrollHeight > card.clientHeight,
                            computedStyle: window.getComputedStyle(card).overflowY
                        });
                    }
                });
            }
            
            // Measure on load and when tutorial opens
            setTimeout(measureTutorialContent, 1000);
            
            // Watch for tutorial opening
            const observer = new MutationObserver((mutations) => {
                mutations.forEach((mutation) => {
                    if (mutation.type === 'attributes' && mutation.attributeName === 'class') {
                        const target = mutation.target;
                        if (target.classList.contains('tutorial-overlay') && !target.classList.contains('hidden')) {
                            console.log('🎓 TUTORIAL OPENED:', target.id);
                            setTimeout(measureTutorialContent, 500);
                        }
                    }
                });
            });
            
            observer.observe(document.body, {
                attributes: true,
                subtree: true,
                attributeFilter: ['class']
            });
            
        }
        
        // Initialize on DOM load
        document.addEventListener('DOMContentLoaded', function() {
            const telegramNativeSupport = initializeTelegramEnvironment();
            applyWebViewOptimizations();
            
            // Store environment info globally
            window.gameEnvironment = {
                isTelegram: isTelegramWebView(),
                hasNativeSwipeControl: telegramNativeSupport,
                fallbackMode: !telegramNativeSupport
            };
            
            // Apply appropriate strategies based on environment
            if (window.gameEnvironment.fallbackMode) {
                applyFallbackStrategies();
            }
            
            // Initialize scroll diagnostics
            initScrollDiagnostics();
            
        });
        
        // GAME STATE (Original code continues)
        
        // Enhanced game state with tutorial
        let gameState = {
            score: 0,
            timeLeft: 45,
            lives: 3,
            isPlaying: false,
            gameTimer: null,
            spawnTimer: null,
            userId: null,
            language: 'english',
            lastUpdate: 0,
            // Tutorial state (simplified - full tutorial moved to /tutorial page)
            tutorialSeen: localStorage.getItem('shabbat-tutorial-seen') === 'true'
        };
        
        // Initialize systems with full screen canvas
        const canvas = document.getElementById('game-canvas');
        canvas.width = window.innerWidth;
        canvas.height = window.innerHeight;
        
        const ctx = canvas.getContext('2d');
        const rabbi = new Rabbi(canvas);
        const fx = new FXSystem(canvas);
        const audio = new AudioSystem();
        
        let gameLoopAnimationId = null;
        
        // Handle window resize
        window.addEventListener('resize', () => {
            canvas.width = window.innerWidth;
            canvas.height = window.innerHeight;
        });
        
        // Game objects
        let gameObjects = [];
        
        // Game items
        const shabbatItems = ['🕯️', '🍞', '🍷', '📖', '🌟', '💎'];
        const forbiddenItems = ['📱', '💵', '💡', '💻', '🚗', '⚡'];
        
        // Telegram WebApp initialization
        if (window.Telegram && window.Telegram.WebApp) {
            const webapp = window.Telegram.WebApp;
            webapp.ready();
            webapp.expand();
            
            const urlParams = new URLSearchParams(window.location.search);
            gameState.userId = urlParams.get('user_id') || webapp.initDataUnsafe?.user?.id;
            gameState.username = urlParams.get('username') || webapp.initDataUnsafe?.user?.username || 'unknown';
            gameState.language = urlParams.get('lang') || 'russian';
            
            console.log('🎮 Game initialized for user:', gameState.userId, '@' + gameState.username);
        }
        
        // Initialize tutorial system after page load
        document.addEventListener('DOMContentLoaded', function() {
            initializeTutorial();
            
            // Apply language to tutorial on load - REMOVED FOR NOW to fix error
        });

        // Tutorial system initialization
        function initializeTutorial() {
            // Check if tutorial has been seen before
            gameState.tutorialSeen = localStorage.getItem('shabbat-tutorial-seen') === 'true';
            
            // Hide REPLAY TUTORIAL button for new users - they'll see tutorial automatically
            updateTutorialButtonVisibility();
        }

        // Update tutorial button visibility based on user experience
        function updateTutorialButtonVisibility() {
            const replayTutorialBtn = document.getElementById('replay-tutorial-btn');
            if (replayTutorialBtn) {
                if (gameState.tutorialSeen) {
                    // Experienced user: show replay tutorial button
                    replayTutorialBtn.style.display = 'block';
                    console.log('👤 Experienced user: REPLAY TUTORIAL button visible');
                } else {
                    // New user: hide replay tutorial button (they'll get tutorial automatically)
                    replayTutorialBtn.style.display = 'none';
                    console.log('🆕 New user: REPLAY TUTORIAL button hidden (tutorial will show automatically)');
                }
            }
            
            // Tutorial multilingual content
            const tutorialContent = {
                english: {
                    items: {
                        candles: { title: '🕯️ Shabbat Candles', text: 'Beginning of Shabbat, light and peace in the home.' },
                        bread: { title: '🍞 Challah', text: 'Double bread — reminder of manna in the desert.' },
                        wine: { title: '🍷 Wine', text: 'Kiddush, blessing and joy.' },
                        book: { title: '📖 Prayer Book/Torah', text: 'Prayers and wisdom of generations.' }
                    },
                    screens: {
                        1: { title: '🕯️ WELCOME 🕯️', text: 'Shalom! Welcome to Kedusha Path.<br>I am your guide. I will show you how to prepare for Shabbat!' },
                        2: { title: '🌟 WHAT IS SHABBAT? 🌟', text: 'Shabbat is a day of rest and holiness.<br>For 3000 years we light candles, sing songs and turn off gadgets 📵.<br>It\'s like cosmic Wi-Fi — you connect to spirituality!' },
                        3: { title: '📖 SYMBOLISM OF OBJECTS 📖', text: 'There are 4 main symbols on the table.<br>Click on any to learn its meaning!' },
                        4: { title: '✅ WHAT TO COLLECT ✅', text: 'Each object brings you sparks of holiness ✨!<br>Collect holy things to prepare for Shabbat!' },
                        5: { title: '❌ WHAT TO AVOID ❌', text: 'This interferes with Shabbat.<br>Touch it — lose a life! Choose holiness instead.' },
                        6: { title: '🎯 TRY IT! 🎯', text: 'Catch 🕯️ and avoid 📱.<br>Ready for the real game?' }
                    }
                },
                russian: {
                    items: {
                        candles: { title: '🕯️ Свечи Шаббата', text: 'Начало Шаббата, свет и мир в доме.' },
                        bread: { title: '🍞 Халы', text: 'Двойной хлеб — напоминание о манне в пустыне.' },
                        wine: { title: '🍷 Вино', text: 'Кидуш, благословение и радость.' },
                        book: { title: '📖 Сидур/Тора', text: 'Молитвы и мудрость поколений.' }
                    },
                    screens: {
                        1: { title: '🕯️ ПРИВЕТСТВИЕ 🕯️', text: 'Шалом! Добро пожаловать в Kedusha Path.<br>Я твой гид. Покажу, как готовиться к Шаббату!' },
                        2: { title: '🌟 ЧТО ТАКОЕ ШАББАТ? 🌟', text: 'Шаббат — это день отдыха и святости.<br>Уже 3000 лет мы зажигаем свечи, поём песни и отключаем гаджеты 📵.<br>Это как cosmic Wi-Fi — подключаешься к духовности!' },
                        3: { title: '📖 СИМВОЛИКА ПРЕДМЕТОВ 📖', text: 'На столе есть 4 главных символа.<br>Нажми на любой, чтобы узнать его значение!' },
                        4: { title: '✅ ЧТО СОБИРАТЬ ✅', text: 'Каждый предмет приносит тебе искры святости ✨!<br>Собирай святые вещи для подготовки к Шаббату!' },
                        5: { title: '❌ ЧЕГО ИЗБЕГАТЬ ❌', text: 'Это мешает Шаббату.<br>Нажмёшь — потеряешь жизнь! Выбирай святость вместо этого.' },
                        6: { title: '🎯 ПОПРОБУЙ! 🎯', text: 'Поймай 🕯️ и избегай 📱.<br>Готов к настоящей игре?' }
                    }
                },
                hebrew: {
                    items: {
                        candles: { title: '🕯️ נרות שבת', text: 'תחילת השבת, אור ושלום בבית.' },
                        bread: { title: '🍞 חלות', text: 'לחם כפול — זכר למן במדבר.' },
                        wine: { title: '🍷 יין', text: 'קידוש, ברכה ושמחה.' },
                        book: { title: '📖 סידור/תורה', text: 'תפילות וחוכמת הדורות.' }
                    },
                    screens: {
                        1: { title: '🕯️ ברוכים הבאים 🕯️', text: 'שלום! ברוכים הבאים לנתיב הקדושה.<br>אני המדריך שלכם. אראה לכם איך מכינים לשבת!' },
                        2: { title: '🌟 מה זה שבת? 🌟', text: 'שבת הוא יום מנוחה וקדושה.<br>כבר 3000 שנה אנחנו מדליקים נרות, שרים ומכבים מכשירים 📵.<br>זה כמו Wi-Fi קוסמי — מתחברים לרוחניות!' },
                        3: { title: '📖 סמליות החפצים 📖', text: 'יש 4 סמלים עיקריים על השולחן.<br>לחצו על כל אחד כדי ללמוד על משמעותו!' },
                        4: { title: '✅ מה לאסוף ✅', text: 'כל חפץ מביא לכם ניצוצות קדושה ✨!<br>אספו דברים קדושים כדי להכין לשבת!' },
                        5: { title: '❌ ממה להימנע ❌', text: 'זה מפריע לשבת.<br>תלחצו — תאבדו חיים! בחרו בקדושה במקום זה.' },
                        6: { title: '🎯 נסו! 🎯', text: 'תפסו 🕯️ והימנעו מ📱.<br>מוכנים למשחק האמיתי?' }
                    }
                }
            };
            
            // Get current tutorial content
            function getCurrentTutorialContent() {
                const lang = gameState.language === 'russian' ? 'russian' : 
                           gameState.language === 'hebrew' ? 'hebrew' : 'english';
                return tutorialContent[lang];
            }
            
            // Tutorial setup removed - now using separate /tutorial page
        }
        
        
        
        
        
        
        
            
        
        
        
        // startTutorial removed - now redirects to /tutorial page

        // Event listeners - FIXED: wrapped in DOMContentLoaded
        document.addEventListener('DOMContentLoaded', function() {
            // Check for autostart parameter from tutorial "В игру" button
            const urlParams = new URLSearchParams(window.location.search);
            const autostart = urlParams.get('autostart');
            
            if (autostart === 'true') {
                // Auto-start game immediately, skip instructions
                setTimeout(() => {
                    document.getElementById('instructions').classList.add('hidden');
                    startGame();
                }, 100);
            }
            document.getElementById('start-btn').addEventListener('click', function() {
                // Check if user is new (tutorial not seen)
                if (!gameState.tutorialSeen) {
                    // New user: redirect to tutorial first
                    const lang = gameState.language || 'russian';
                    console.log('🎓 New user detected, redirecting to tutorial with language:', lang);
                    window.location.href = `/tutorial?lang=${lang}`;
                } else {
                    // Experienced user: start game directly
                    console.log('🎮 Experienced user, starting game directly');
                    document.getElementById('instructions').classList.add('hidden');
                    startGame();
                }
            });

            // Replay Tutorial Button Handler
            document.getElementById('replay-tutorial-btn').addEventListener('click', function() {
                // Navigate to separate tutorial page - clean architecture
                const lang = gameState.language || 'russian';
                window.location.href = `/tutorial?lang=${lang}`;
            });

            document.getElementById('play-again').addEventListener('click', function() {
                // FIXED: Start game directly, not return to instructions
                document.getElementById('game-over').classList.add('hidden');
                startGame(); // Start game immediately
            });

            // Replay Tutorial from End Screen
            document.getElementById('replay-tutorial-end').addEventListener('click', function() {
                // Navigate to tutorial page with current language
                const currentUrl = new URL(window.location);
                const lang = gameState.language || 'russian';
                window.location.href = `/tutorial?lang=${lang}`;
            });

            document.getElementById('share-telegram').addEventListener('click', function(e) {
                e.preventDefault();
                console.log('🔄 Share button clicked, score:', gameState.score);
                shareGameScore(gameState.score, gameState.language);
            });

            // Game Over Close Button Handler
            document.getElementById('game-over-close').addEventListener('click', function() {
                // Hide game-over screen and return to main instructions screen
                document.getElementById('game-over').classList.add('hidden');
                document.getElementById('instructions').classList.remove('hidden');
                console.log('❌ Game over screen closed, returning to main screen');
            });

            // Add canvas click handlers
            canvas.addEventListener('click', canvasClickHandler);
            canvas.addEventListener('touchstart', function(e) {
                e.preventDefault();
                const touch = e.touches[0];
                canvasClickHandler(touch);
            });
        });

        // Canvas click handling - simplified without pause/resume
        function canvasClickHandler(e) {
            if (!gameState.isPlaying) return; // Only check if game is playing
            
            const rect = canvas.getBoundingClientRect();
            const clickX = (e.clientX - rect.left) * (canvas.width / rect.width);
            const clickY = (e.clientY - rect.top) * (canvas.height / rect.height);
            
            // Check if clicked on any object (expanded click area for better UX)
            for (let obj of gameObjects) {
                const clickBuffer = 15; // Extra pixels around object for easier tapping
                if (clickX >= obj.x - clickBuffer && clickX <= obj.x + obj.size + clickBuffer &&
                    clickY >= obj.y - clickBuffer && clickY <= obj.y + obj.size + clickBuffer && !obj.clicked) {
                    
                    obj.clicked = true;
                    
                    if (obj.isGood) {
                        // Collected good item - Kedusha Spark animation
                        gameState.score += 2;
                        gameState.itemsCollected++; // Track items collected for analytics
                        fx.createKedushaSpark(obj.x + obj.size/2, obj.y + obj.size/2);
                        audio.playCollectSound();
                        rabbi.celebrate();
                        // Rabbi feedback removed for cleaner UI
                        
                        // Item scaling animation (1.0 → 1.2 → 1.0)
                        obj.scaleAnimation = { scale: 1.0, timer: 200, direction: 1 };
                        obj.emoji = '✨';
                    } else {
                        // Clicked forbidden item - Chill Blast animation
                        gameState.lives--;
                        gameState.score = Math.max(0, gameState.score - 1);
                        gameState.mistakesMade++; // Track mistakes for analytics
                        fx.createChillBlast(obj.x + obj.size/2, obj.y + obj.size/2);
                        audio.playMistakeSound();
                        rabbi.disappointedButKind();
                        // Rabbi feedback removed for cleaner UI
                        
                        // Item shake/squash animation (1.0 → 0.8 → 1.0)
                        obj.scaleAnimation = { scale: 1.0, timer: 200, direction: -1, rotation: 0 };
                        obj.emoji = '💥';
                        
                        if (gameState.lives <= 0) {
                            endGame();
                            return;
                        }
                    }
                    updateHUD();
                    break;
                }
            }
        }
        
        // Canvas event listeners moved to DOMContentLoaded wrapper above


        function startGame() {
            gameState.isPlaying = true;
            gameState.score = 0;
            gameState.timeLeft = 45;
            gameState.lives = 3;
            gameState.lastUpdate = performance.now();
            gameState.gameStartTime = Date.now(); // Track game start time for analytics
            gameState.itemsCollected = 0; // Track collected items
            gameState.mistakesMade = 0; // Track mistakes
            gameObjects = [];
            
            fx.clear();
            updateHUD();
            
            // Send GAME_STARTED analytics
            sendGameAnalytics('GAME_STARTED', {
                after_tutorial: checkIfFromTutorial(),
                timestamp: new Date().toISOString()
            });
            
            // Rabbi welcome
            rabbi.excited();
            // Rabbi start message removed for cleaner UI
            audio.playStartSound();
            
            // Game timer
            gameState.gameTimer = setInterval(() => {
                gameState.timeLeft--;
                updateHUD();
                
                if (gameState.timeLeft <= 0) {
                    endGame();
                }
            }, 1000);
            
            // Spawn objects
            gameState.spawnTimer = setInterval(spawnObject, 800);
            
            // Game loop
            gameLoop();
            
        }

        function spawnObject() {
            if (!gameState.isPlaying) return;
            
            const isGood = Math.random() > 0.4;
            const items = isGood ? shabbatItems : forbiddenItems;
            const emoji = items[Math.floor(Math.random() * items.length)];
            
            gameObjects.push({
                x: Math.random() * (canvas.width - 60),
                y: -50,
                emoji: emoji,
                isGood: isGood,
                speed: 2 + Math.random() * 3,
                size: 40,
                clicked: false
            });
        }

        function gameLoop() {
            if (!gameState.isPlaying) return;
            
            const now = performance.now();
            const deltaTime = now - gameState.lastUpdate;
            gameState.lastUpdate = now;
            
            // Clear canvas
            ctx.clearRect(0, 0, canvas.width, canvas.height);
            
            // Parallax sunset background for Shabbat atmosphere
            drawParallaxBackground(ctx, canvas.width, canvas.height, now);
            
            for (let i = gameObjects.length - 1; i >= 0; i--) {
                const obj = gameObjects[i];
                obj.y += obj.speed;
                
                // Draw object with themed glow effects
                drawItemWithGlow(ctx, obj, now);
                
                // Remove if off screen
                if (obj.y > canvas.height + 50) {
                    if (obj.isGood && !obj.clicked) {
                        gameState.lives--;
                        audio.playMistakeSound();
                        rabbi.disappointedButKind();
                        // Rabbi warning removed for cleaner UI
                        updateHUD();
                        if (gameState.lives <= 0) {
                            endGame();
                            return;
                        }
                    }
                    gameObjects.splice(i, 1);
                }
            }
            
            // Update systems
            fx.update(deltaTime);
            rabbi.update(deltaTime);
            
            // Render systems
            fx.render();
            rabbi.render();
            
            // Continue game loop always when playing
            if (gameState.isPlaying) {
                gameLoopAnimationId = requestAnimationFrame(gameLoop);
            }
        }

        function updateHUD() {
            // Update score with flash animation
            const scoreEl = document.getElementById('score');
            const prevScore = parseInt(scoreEl.textContent.replace('Score: ', '') || '0');
            if (gameState.score > prevScore) {
                scoreEl.classList.add('flash');
                setTimeout(() => scoreEl.classList.remove('flash'), 600);
            }
            scoreEl.textContent = `Score: ${gameState.score}`;
            
            // Update timer with pulse animation when < 5 seconds
            const timerEl = document.getElementById('timer');
            timerEl.textContent = `Time: ${gameState.timeLeft}`;
            if (gameState.timeLeft <= 5 && gameState.timeLeft > 0) {
                timerEl.classList.add('pulse');
            } else {
                timerEl.classList.remove('pulse');
            }
            
            // Update lives with shake animation when lost
            const livesEl = document.getElementById('lives');
            const prevLives = (livesEl.textContent.match(/❤️/g) || []).length;
            if (gameState.lives < prevLives) {
                livesEl.classList.add('shake');
                setTimeout(() => livesEl.classList.remove('shake'), 500);
            }
            livesEl.textContent = `Lives: ${'❤️'.repeat(gameState.lives)}`;
        }

        function endGame() {
            gameState.isPlaying = false;
            clearInterval(gameState.gameTimer);
            clearInterval(gameState.spawnTimer);
            
            // Calculate game duration for analytics
            const gameDuration = gameState.gameStartTime ? (Date.now() - gameState.gameStartTime) / 1000 : 0;
            
            // Send GAME_COMPLETED analytics with detailed data
            sendGameAnalytics('GAME_COMPLETED', {
                score: gameState.score,
                duration: gameDuration,
                items_collected: gameState.itemsCollected || 0,
                mistakes: gameState.mistakesMade || 0,
                final_lives: gameState.lives,
                completed: true,
                timestamp: new Date().toISOString()
            });
            
            // Check for achievements
            checkAndSendAchievements(gameState.score, gameState.itemsCollected);
            
            // Audio and visual feedback
            audio.playEndSound();
            rabbi.celebrate();
            
            // Show final results
            document.getElementById('final-score').textContent = gameState.score;
            document.getElementById('game-message').textContent = formatEndMessage(gameState.score, gameState.language);
            
            // Rabbi final message - REMOVED to clean up final screen UI
            
            document.getElementById('game-over').classList.remove('hidden');
            
            // Send score to bot
            if (gameState.userId) {
                sendScoreToBot(gameState.userId, gameState.score);
            }
        }

        // ========== ANALYTICS FUNCTIONS ==========
        
        // Send game analytics to server
        async function sendGameAnalytics(eventType, eventData = {}) {
            try {
                // Get user data from gameState (already populated from Telegram)
                const userData = {
                    user_id: gameState.userId || Date.now(),
                    username: gameState.username || 'unknown',
                    language: gameState.language || 'russian'
                };
                
                const analyticsData = {
                    event_type: eventType,
                    ...userData,
                    ...eventData
                };
                
                const response = await fetch('/api/game-analytics', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(analyticsData)
                });
                
                if (response.ok) {
                    console.log(`📊 Game analytics sent: ${eventType}`, userData);
                } else {
                    console.warn(`⚠️ Game analytics failed: ${eventType}`);
                }
            } catch (error) {
                console.warn(`⚠️ Game analytics error: ${error.message}`);
            }
        }
        
        // Check if user came from tutorial
        function checkIfFromTutorial() {
            const urlParams = new URLSearchParams(window.location.search);
            return urlParams.get('from_tutorial') === 'true';
        }
        
        // Check and send achievement notifications
        function checkAndSendAchievements(score, itemsCollected) {
            // High score achievement
            if (score >= 20) {
                sendGameAnalytics('GAME_ACHIEVEMENT', {
                    achievement_type: 'high_score',
                    score: score,
                    threshold: 20
                });
            }
            
            // Perfect collector achievement (collected 15+ items)
            if (itemsCollected >= 15) {
                sendGameAnalytics('GAME_ACHIEVEMENT', {
                    achievement_type: 'perfect_collector',
                    items_collected: itemsCollected,
                    threshold: 15
                });
            }
            
            // Shabbat master achievement (score 25+)
            if (score >= 25) {
                sendGameAnalytics('GAME_ACHIEVEMENT', {
                    achievement_type: 'shabbat_master',
                    score: score,
                    threshold: 25
                });
            }
        }

        async function sendScoreToBot(userId, score) {
            try {
                const response = await fetch('/game/score', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ user_id: userId, score: score })
                });
                
                if (response.ok) {
                    console.log('🎯 Score sent successfully:', score);
                }
            } catch (error) {
                console.error('❌ Score sending error:', error);
            }
        }

        // Share game score with friends via Telegram - Updated to use bot API
        async function shareGameScore(score, language = 'russian') {
            try {
                // Send share request to bot API
                const response = await fetch('/game/share', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ 
                        user_id: gameState.userId, 
                        score: score, 
                        language: language 
                    })
                });
                
                if (response.ok) {
                    const shareData = await response.json();
                    console.log('📤 Share data received:', shareData);
                    
                    // Open Telegram share URL - iOS compatible
                    if (shareData.share_url) {
                        // Use Telegram WebApp API for better iOS compatibility
                        if (window.Telegram && window.Telegram.WebApp && window.Telegram.WebApp.openTelegramLink) {
                            console.log('📱 Using Telegram WebApp API for iOS/mobile');
                            window.Telegram.WebApp.openTelegramLink(shareData.share_url);
                        } else {
                            console.log('🖥️ Using window.open for desktop');
                            window.open(shareData.share_url, '_blank');
                        }
                        console.log('📤 Score shared successfully via Telegram');
                    } else {
                        throw new Error('No share URL received');
                    }
                } else {
                    throw new Error(`Share API error: ${response.status}`);
                }
                
            } catch (error) {
                console.error('❌ Share error:', error);
                
                // Fallback: Use centralized share builder for consistency
                const fallbackMessage = buildShareMessage(score, language, false); // No URL in message
                const gameUrl = 'https://torah-project-jobjoyclub.replit.app';
                copyGameLinkToClipboard(gameUrl, fallbackMessage);
            }
        }

        // URL DEDUPLICATION GUARD - removes existing URLs from text to prevent duplicates
        function stripUrl(text, url) {
            if (!text || !url) return text;
            
            // Remove exact URL matches
            let cleanText = text.replace(new RegExp(url.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'), 'gi'), '');
            
            // Remove common URL patterns that might appear
            cleanText = cleanText.replace(/https?:\/\/[^\s]+/gi, '');
            
            // Clean up extra whitespace and newlines
            cleanText = cleanText.replace(/\n\s*\n/g, '\n').trim();
            
            return cleanText;
        }
        
        // CENTRALIZED share builder - constructs message safely without URL duplication
        function buildShareMessage(score, language, includeUrl = false) {
            const baseMessages = {
                russian: `🏆 Я набрал ${score} очков в Shabbat Runner!\n\n🕯️ Попробуй себя в изучении еврейских традиций через игру!\n🎮 Собирай святые предметы и изучай Шаббат!\n\n✨ Проверь свои знания о еврейской культуре!`,
                english: `🏆 I scored ${score} points in Shabbat Runner!\n\n🕯️ Try learning Jewish traditions through gaming!\n🎮 Collect holy items and learn about Shabbat!\n\n✨ Test your knowledge of Jewish culture!`,
                hebrew: `🏆 קיבלתי ${score} נקודות ב-Shabbat Runner!\n\n🕯️ נסו ללמוד מסורות יהודיות דרך משחק!\n🎮 אספו פריטים קדושים ולמדו על שבת!\n\n✨ בדקו את הידע שלכם על התרבות היהודית!`
            };
            
            const gameUrl = 'https://torah-project-jobjoyclub.replit.app';
            const baseText = baseMessages[language] || baseMessages.russian;
            
            return includeUrl ? `${baseText}\n\n${gameUrl}` : baseText;
        }
        
        // SAFE clipboard copy with deduplication
        function copyGameLinkToClipboard(url, message) {
            // Strip any existing URLs from message to prevent duplication
            const cleanMessage = stripUrl(message, url);
            const fullText = `${cleanMessage}\n\n${url}`;
            
            if (navigator.clipboard) {
                navigator.clipboard.writeText(fullText).then(() => {
                    alert('🔗 Ссылка скопирована в буфер обмена!');
                }).catch(() => {
                    fallbackCopyText(fullText);
                });
            } else {
                fallbackCopyText(fullText);
            }
        }

        // Manual text selection fallback
        function fallbackCopyText(text) {
            const textArea = document.createElement('textarea');
            textArea.value = text;
            textArea.style.position = 'fixed';
            textArea.style.opacity = '0';
            document.body.appendChild(textArea);
            textArea.select();
            
            try {
                document.execCommand('copy');
                alert('🔗 Ссылка скопирована в буфер обмена!');
            } catch (err) {
                alert('❌ Не удалось скопировать ссылку');
            }
            
            document.body.removeChild(textArea);
        }
