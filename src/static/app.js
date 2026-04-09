const reviewInput = document.getElementById('reviewInput');
const predictBtn = document.getElementById('predictBtn');
const clearBtn = document.getElementById('clearBtn');
const resultBox = document.getElementById('resultBox');
const sentimentText = document.getElementById('sentimentText');
const resultText = document.getElementById('resultText');
const confidenceFill = document.getElementById('confidenceFill');
const confidenceValue = document.getElementById('confidenceValue');
const apiStatus = document.getElementById('apiStatus');

const sampleButtons = document.querySelectorAll('[data-sample]');

const setLoading = (isLoading) => {
  predictBtn.disabled = isLoading;
  predictBtn.textContent = isLoading ? 'Analyzing...' : 'Analyze sentiment';
};

const renderResult = (sentiment, confidence) => {
  const value = Math.max(0, Math.min(100, Math.round(confidence * 100)));
  const isPositive = sentiment.toLowerCase() === 'positive';

  resultBox.hidden = false;
  sentimentText.textContent = sentiment;
  sentimentText.className = isPositive ? 'positive' : 'negative';
  resultText.textContent = isPositive
    ? 'The review looks positive. The model detected supportive language.'
    : 'The review looks negative. The model detected critical language.';
  confidenceFill.style.width = `${value}%`;
  confidenceValue.textContent = `${value}%`;
};

const checkApi = async () => {
  try {
    const response = await fetch('/health');
    if (!response.ok) {
      throw new Error('Health check failed');
    }

    apiStatus.textContent = 'API ready';
    apiStatus.style.color = '#77e0bc';
  } catch (error) {
    apiStatus.textContent = 'Offline';
    apiStatus.style.color = '#ff7c8a';
  }
};

predictBtn.addEventListener('click', async () => {
  const text = reviewInput.value.trim();

  if (!text) {
    reviewInput.focus();
    return;
  }

  setLoading(true);

  try {
    const response = await fetch('/predict', {
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
    sentimentText.textContent = 'Error';
    sentimentText.className = 'negative';
    resultText.textContent = 'The API could not return a prediction right now.';
    confidenceFill.style.width = '0%';
    confidenceValue.textContent = '--';
  } finally {
    setLoading(false);
  }
});

clearBtn.addEventListener('click', () => {
  reviewInput.value = '';
  resultBox.hidden = true;
  reviewInput.focus();
});

sampleButtons.forEach((button) => {
  button.addEventListener('click', () => {
    reviewInput.value = button.dataset.sample || '';
    reviewInput.focus();
  });
});

checkApi();