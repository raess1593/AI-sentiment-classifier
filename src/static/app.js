const reviewInput = document.getElementById('reviewInput');
const predictBtn = document.getElementById('predictBtn');
const clearBtn = document.getElementById('clearBtn');
const resultBox = document.getElementById('resultBox');
const sentimentText = document.getElementById('sentimentText');
const resultText = document.getElementById('resultText');
const confidenceFill = document.getElementById('confidenceFill');
const confidenceValue = document.getElementById('confidenceValue');
const confidenceGauge = document.getElementById('confidenceGauge');
const apiStatus = document.getElementById('apiStatus');
const charCount = document.getElementById('charCount');

const sampleButtons = document.querySelectorAll('[data-sample]');
const apiCandidates = [
  '',
  'http://127.0.0.1:8000',
  'http://localhost:8000',
  'http://127.0.0.1:10000',
  'http://localhost:10000',
];

let apiBaseUrl = '';

const setLoading = (isLoading) => {
  predictBtn.disabled = isLoading;
  predictBtn.textContent = isLoading ? 'Analyzing...' : 'Analyze sentiment';
};

const setResultState = (state) => {
  resultBox.classList.remove('state-positive', 'state-negative', 'state-error');

  if (state) {
    resultBox.classList.add(state);
  }
};

const buildApiUrl = (path) => `${apiBaseUrl}${path}`;

const findApiBaseUrl = async () => {
  for (const candidate of apiCandidates) {
    try {
      const response = await fetch(`${candidate}/health`, { cache: 'no-store' });

      if (response.ok) {
        apiBaseUrl = candidate;
        return candidate;
      }
    } catch (error) {
      continue;
    }
  }

  apiBaseUrl = '';
  return '';
};

const setGauge = (value, isPositive) => {
  const safeValue = Math.max(0, Math.min(100, value));
  const angle = `${Math.round((safeValue / 100) * 360)}deg`;

  confidenceGauge.style.setProperty('--fill', angle);
  confidenceGauge.style.background = isPositive
    ? `conic-gradient(#52d5ab ${angle}, rgba(255,255,255,0.12) ${angle})`
    : `conic-gradient(#ff6f89 ${angle}, rgba(255,255,255,0.12) ${angle})`;
  confidenceValue.style.color = isPositive ? '#99ecd3' : '#ff9eb0';
};

const renderResult = (sentiment, confidence) => {
  const value = Math.max(0, Math.min(100, Math.round(confidence * 100)));
  const isPositive = sentiment.toLowerCase() === 'positive';

  resultBox.hidden = false;
  setResultState(isPositive ? 'state-positive' : 'state-negative');
  sentimentText.textContent = sentiment;
  sentimentText.className = isPositive ? 'positive' : 'negative';
  resultText.textContent = isPositive
    ? 'Strong positive sentiment detected. The language indicates satisfaction and approval.'
    : 'Negative sentiment detected. The language reflects dissatisfaction or criticism.';
  confidenceFill.style.width = `${value}%`;
  confidenceFill.style.background = isPositive
    ? 'linear-gradient(90deg, #52d5ab, #6db0ff)'
    : 'linear-gradient(90deg, #ff9a76, #ff6f89)';
  confidenceValue.textContent = `${value}%`;
  setGauge(value, isPositive);
};

const checkApi = async () => {
  try {
    const baseUrl = await findApiBaseUrl();

    if (!baseUrl && window.location.protocol === 'http:' && window.location.port !== '10000') {
      throw new Error('Health check failed');
    }

    const response = await fetch(buildApiUrl('/health'), { cache: 'no-store' });
    const data = await response.json();
    apiStatus.textContent = data.model_loaded ? 'API ready' : 'Model unavailable';
    apiStatus.style.color = data.model_loaded ? '#8de8cb' : '#ff9eb0';
    apiStatus.style.borderColor = data.model_loaded
      ? 'rgba(82, 213, 171, 0.34)'
      : 'rgba(255, 111, 137, 0.34)';
    apiStatus.style.background = data.model_loaded
      ? 'rgba(82, 213, 171, 0.12)'
      : 'rgba(255, 111, 137, 0.12)';
  } catch (error) {
    apiStatus.textContent = 'Offline';
    apiStatus.style.color = '#ff9eb0';
    apiStatus.style.borderColor = 'rgba(255, 111, 137, 0.34)';
    apiStatus.style.background = 'rgba(255, 111, 137, 0.12)';
  }
};

reviewInput.addEventListener('input', () => {
  charCount.textContent = `${reviewInput.value.length}/1000`;
});

reviewInput.addEventListener('keydown', (event) => {
  if (event.key === 'Enter' && !event.shiftKey) {
    event.preventDefault();
    predictBtn.click();
  }
});

predictBtn.addEventListener('click', async () => {
  const text = reviewInput.value.trim();

  if (!text) {
    reviewInput.focus();
    return;
  }

  setLoading(true);

  try {
    if (!apiBaseUrl) {
      await findApiBaseUrl();
    }

    const response = await fetch(buildApiUrl('/predict'), {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ text }),
    });

    if (!response.ok) {
      throw new Error('Prediction request failed');
    }

    const data = await response.json();
    renderResult(data.sentiment, data.confidence);
  } catch (error) {
    resultBox.hidden = false;
    setResultState('state-error');
    sentimentText.textContent = 'Error';
    sentimentText.className = 'negative';
    resultText.textContent = 'The API could not return a prediction right now. Check backend status and model availability.';
    confidenceFill.style.width = '0%';
    confidenceFill.style.background = 'linear-gradient(90deg, #ff9a76, #ff6f89)';
    confidenceValue.textContent = '--';
    setGauge(0, false);
  } finally {
    setLoading(false);
  }
});

clearBtn.addEventListener('click', () => {
  reviewInput.value = '';
  charCount.textContent = '0/1000';
  resultBox.hidden = true;
  setResultState('');
  sentimentText.className = '';
  reviewInput.focus();
});

sampleButtons.forEach((button) => {
  button.addEventListener('click', () => {
    reviewInput.value = button.dataset.sample || '';
    reviewInput.focus();
    charCount.textContent = `${reviewInput.value.length}/1000`;
  });
});

setGauge(0, true);
checkApi();