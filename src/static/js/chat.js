/**
 * LLMチャットアプリのフロントエンド機能を実装するJavaScriptファイル
 */

// Socket.IOの接続を確立
const socket = io();

// DOM要素の取得
const modelSelection = document.getElementById('model-selection');
const chatContainer = document.getElementById('chat-container');
const settingsContainer = document.getElementById('settings-container');
const modelManagerContainer = document.getElementById('model-manager-container');
const modelList = document.getElementById('model-list');
const modelStatus = document.getElementById('model-status');
const currentModelName = document.getElementById('current-model-name');
const changeModelBtn = document.getElementById('change-model-btn');
const modelManagerBtn = document.getElementById('model-manager-btn');
const settingsBtn = document.getElementById('settings-btn');
const closeSettingsBtn = document.getElementById('close-settings-btn');
const closeModelManagerBtn = document.getElementById('close-model-manager-btn');
const refreshModelManagerBtn = document.getElementById('refresh-model-manager-btn');
const runningModels = document.getElementById('running-models');
const gpuInfo = document.getElementById('gpu-info');
const chatForm = document.getElementById('chat-form');
const messageInput = document.getElementById('message-input');
const chatMessages = document.getElementById('chat-messages');
const sendButton = document.getElementById('send-button');
const statusText = document.getElementById('status-text');
const statusDot = document.querySelector('.status-dot');

// 設定関連の要素
const temperatureSlider = document.getElementById('temperature');
const temperatureValue = document.getElementById('temperature-value');
const topPSlider = document.getElementById('top-p');
const topPValue = document.getElementById('top-p-value');
const topKSlider = document.getElementById('top-k');
const topKValue = document.getElementById('top-k-value');
const contextLengthSlider = document.getElementById('context-length');
const contextLengthValue = document.getElementById('context-length-value');
const repeatPenaltySlider = document.getElementById('repeat-penalty');
const repeatPenaltyValue = document.getElementById('repeat-penalty-value');
const resetSettingsBtn = document.getElementById('reset-settings-btn');
const saveSettingsBtn = document.getElementById('save-settings-btn');

// アプリケーションの状態
let currentModel = null;
let isProcessing = false;
let modelParams = {
    temperature: 0.7,
    top_p: 0.9,
    top_k: 40,
    context_length: 4096,
    repeat_penalty: 1.1
};

// デフォルトのパラメータ設定
const defaultParams = {
    temperature: 0.7,
    top_p: 0.9,
    top_k: 40,
    context_length: 4096,
    repeat_penalty: 1.1
};

// 初期化
document.addEventListener('DOMContentLoaded', () => {
    // モデル一覧を取得
    fetchModels();
    
    // モデルパラメータを取得
    fetchModelParams();
    
    // イベントリスナーの設定
    setupEventListeners();
});

/**
 * モデル一覧を取得する関数
 */
async function fetchModels() {
    try {
        const response = await fetch('/api/models');
        const data = await response.json();
        
        if (data.models && data.models.length > 0) {
            displayModels(data.models);
            modelStatus.textContent = 'モデルを選択してください';
        } else {
            modelList.innerHTML = `
                <div class="model-error">
                    <p>利用可能なモデルがありません。ollamaサーバーが起動しているか確認してください。</p>
                    <button onclick="fetchModels()" class="model-select-btn">再試行</button>
                </div>
            `;
            modelStatus.textContent = 'モデルが見つかりません';
        }
    } catch (error) {
        console.error('モデル一覧の取得に失敗しました:', error);
        modelList.innerHTML = `
            <div class="model-error">
                <p>モデル一覧の取得に失敗しました。ollamaサーバーが起動しているか確認してください。</p>
                <button onclick="fetchModels()" class="model-select-btn">再試行</button>
            </div>
        `;
        modelStatus.textContent = 'サーバーに接続できません';
    }
}

/**
 * モデルパラメータを取得する関数
 */
async function fetchModelParams() {
    try {
        const response = await fetch('/api/model_params');
        const data = await response.json();
        
        if (data.params) {
            modelParams = data.params;
            updateSettingsUI();
        }
    } catch (error) {
        console.error('モデルパラメータの取得に失敗しました:', error);
    }
}

/**
 * 起動中のモデル一覧を取得する関数
 */
async function fetchRunningModels() {
    try {
        const response = await fetch('/api/running_models');
        const data = await response.json();
        
        if (data.models) {
            displayRunningModels(data.models);
        } else {
            runningModels.innerHTML = `
                <div class="no-models-message">
                    <p>起動中のモデルがありません。</p>
                </div>
            `;
        }
    } catch (error) {
        console.error('起動中のモデル一覧の取得に失敗しました:', error);
        runningModels.innerHTML = `
            <div class="model-error">
                <p>起動中のモデル一覧の取得に失敗しました。ollamaサーバーが起動しているか確認してください。</p>
                <button onclick="refreshModelManager()" class="model-select-btn">再試行</button>
            </div>
        `;
    }
}

/**
 * GPU情報を取得する関数
 */
async function fetchGpuInfo() {
    try {
        const response = await fetch('/api/gpu_info');
        const data = await response.json();
        
        if (data.gpus && data.gpus.length > 0) {
            displayGpuInfo(data.gpus);
        } else {
            gpuInfo.innerHTML = `
                <div class="no-gpu-message">
                    <p>GPU情報を取得できませんでした。GPUが搭載されていないか、ドライバが正しくインストールされていない可能性があります。</p>
                </div>
            `;
        }
    } catch (error) {
        console.error('GPU情報の取得に失敗しました:', error);
        gpuInfo.innerHTML = `
            <div class="model-error">
                <p>GPU情報の取得に失敗しました。</p>
                <button onclick="refreshModelManager()" class="model-select-btn">再試行</button>
            </div>
        `;
    }
}

/**
 * モデル管理画面を更新する関数
 */
async function refreshModelManager() {
    // ローディング表示
    runningModels.innerHTML = `
        <div class="loading-spinner">
            <div class="spinner"></div>
            <p>モデルを読み込み中...</p>
        </div>
    `;
    
    gpuInfo.innerHTML = `
        <div class="loading-spinner">
            <div class="spinner"></div>
            <p>GPU情報を読み込み中...</p>
        </div>
    `;
    
    // 起動中のモデルとGPU情報を取得
    await Promise.all([
        fetchRunningModels(),
        fetchGpuInfo()
    ]);
}

/**
 * モデル一覧を表示する関数
 *
 * @param {Array} models - モデル情報の配列
 */
function displayModels(models) {
    modelList.innerHTML = '';
    
    models.forEach(model => {
        const modelCard = document.createElement('div');
        modelCard.classList.add('model-card');
        
        // モデルサイズをフォーマット
        const sizeInGB = model.size ? (model.size / (1024 * 1024 * 1024)).toFixed(2) + ' GB' : '不明';
        
        modelCard.innerHTML = `
            <div class="model-info">
                <div class="model-name">${model.name}</div>
                <div class="model-details">サイズ: ${sizeInGB}</div>
            </div>
            <button class="model-select-btn" data-model="${model.name}">選択</button>
        `;
        
        modelList.appendChild(modelCard);
        
        // 選択ボタンのイベントリスナー
        const selectBtn = modelCard.querySelector('.model-select-btn');
        selectBtn.addEventListener('click', () => selectModel(model.name));
    });
}

/**
 * 起動中のモデル一覧を表示する関数
 *
 * @param {Array} models - 起動中のモデル情報の配列
 */
function displayRunningModels(models) {
    if (models.length === 0) {
        runningModels.innerHTML = `
            <div class="no-models-message">
                <p>起動中のモデルがありません。</p>
            </div>
        `;
        return;
    }
    
    runningModels.innerHTML = '';
    
    models.forEach(model => {
        const modelCard = document.createElement('div');
        modelCard.classList.add('running-model-card');
        
        modelCard.innerHTML = `
            <div class="running-model-info">
                <div class="running-model-name">${model.model}</div>
                <div class="running-model-id">ID: ${model.id}</div>
            </div>
            <button class="kill-model-btn" data-id="${model.id}">終了</button>
        `;
        
        runningModels.appendChild(modelCard);
        
        // 終了ボタンのイベントリスナー
        const killBtn = modelCard.querySelector('.kill-model-btn');
        killBtn.addEventListener('click', () => killModel(model.id));
    });
}

/**
 * GPU情報を表示する関数
 *
 * @param {Array} gpus - GPU情報の配列
 */
function displayGpuInfo(gpus) {
    if (gpus.length === 0) {
        gpuInfo.innerHTML = `
            <div class="no-gpu-message">
                <p>GPU情報を取得できませんでした。GPUが搭載されていないか、ドライバが正しくインストールされていない可能性があります。</p>
            </div>
        `;
        return;
    }
    
    gpuInfo.innerHTML = '';
    
    gpus.forEach(gpu => {
        const gpuCard = document.createElement('div');
        gpuCard.classList.add('gpu-card');
        
        // メモリ使用量をフォーマット
        const memUsed = gpu.memory_used ? `${gpu.memory_used.toFixed(0)} MB` : '不明';
        const memTotal = gpu.memory_total ? `${gpu.memory_total.toFixed(0)} MB` : '不明';
        const memPercent = gpu.memory_used_percent ? gpu.memory_used_percent.toFixed(1) : 0;
        
        gpuCard.innerHTML = `
            <div class="gpu-header">
                <div class="gpu-name">${gpu.name} (GPU ${gpu.index})</div>
                <div class="gpu-utilization">${gpu.utilization.toFixed(1)}%</div>
            </div>
            <div class="gpu-memory">メモリ使用量: ${memUsed} / ${memTotal} (${memPercent}%)</div>
            <div class="gpu-progress-bar">
                <div class="gpu-progress" style="width: ${gpu.utilization}%"></div>
            </div>
        `;
        
        gpuInfo.appendChild(gpuCard);
    });
}

/**
 * モデルを選択する関数
 *
 * @param {string} modelName - 選択するモデル名
 */
async function selectModel(modelName) {
    try {
        modelStatus.textContent = 'モデルを選択中...';
        
        const response = await fetch('/api/select_model', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ model: modelName })
        });
        
        const data = await response.json();
        
        if (data.success) {
            currentModel = modelName;
            currentModelName.textContent = modelName;
            
            // チャット画面に切り替え
            modelSelection.style.display = 'none';
            chatContainer.style.display = 'flex';
            
            // チャットメッセージをクリア
            chatMessages.innerHTML = `
                <div class="message system-message">
                    <div class="message-content">
                        モデル「${modelName}」が選択されました。メッセージを入力してください。
                    </div>
                </div>
            `;
            
            // モデル情報があれば表示
            if (data.model_info) {
                console.log('モデル情報:', data.model_info);
            }
            
            // 接続状態を更新
            updateConnectionStatus('ready');
        } else {
            modelStatus.textContent = `エラー: ${data.error || 'モデルの選択に失敗しました'}`;
        }
    } catch (error) {
        console.error('モデルの選択に失敗しました:', error);
        modelStatus.textContent = 'モデルの選択に失敗しました';
    }
}

/**
 * モデルを終了する関数
 *
 * @param {string} modelId - 終了するモデルのID
 */
async function killModel(modelId) {
    try {
        const response = await fetch('/api/kill_model', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ id: modelId })
        });
        
        const data = await response.json();
        
        if (data.success) {
            // モデル管理画面を更新
            refreshModelManager();
            
            // 成功メッセージを表示
            addMessageToUI('system', `モデル(ID: ${modelId})を終了しました。`);
        } else {
            console.error('モデルの終了に失敗しました');
            addMessageToUI('system', `モデルの終了に失敗しました: ${data.error || 'エラーが発生しました'}`);
        }
    } catch (error) {
        console.error('モデルの終了に失敗しました:', error);
        addMessageToUI('system', `モデルの終了に失敗しました: ${error.message}`);
    }
}

/**
 * モデルパラメータを更新する関数
 */
async function updateModelParams() {
    try {
        const response = await fetch('/api/model_params', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ params: modelParams })
        });
        
        const data = await response.json();
        
        if (data.success) {
            modelParams = data.params;
            return true;
        } else {
            console.error('パラメータの更新に失敗しました');
            return false;
        }
    } catch (error) {
        console.error('パラメータの更新に失敗しました:', error);
        return false;
    }
}

/**
 * 設定UIを更新する関数
 */
function updateSettingsUI() {
    temperatureSlider.value = modelParams.temperature;
    temperatureValue.textContent = modelParams.temperature;
    
    topPSlider.value = modelParams.top_p;
    topPValue.textContent = modelParams.top_p;
    
    topKSlider.value = modelParams.top_k;
    topKValue.textContent = modelParams.top_k;
    
    contextLengthSlider.value = modelParams.context_length;
    contextLengthValue.textContent = modelParams.context_length;
    
    repeatPenaltySlider.value = modelParams.repeat_penalty;
    repeatPenaltyValue.textContent = modelParams.repeat_penalty;
}

/**
 * イベントリスナーを設定する関数
 */
function setupEventListeners() {
    // モデル変更ボタンのイベントリスナー
    changeModelBtn.addEventListener('click', () => {
        chatContainer.style.display = 'none';
        modelSelection.style.display = 'flex';
        fetchModels();
    });
    
    // モデル管理ボタンのイベントリスナー
    modelManagerBtn.addEventListener('click', () => {
        modelManagerContainer.style.display = 'flex';
        refreshModelManager();
    });
    
    // モデル管理を閉じるボタンのイベントリスナー
    closeModelManagerBtn.addEventListener('click', () => {
        modelManagerContainer.style.display = 'none';
    });
    
    // モデル管理を更新するボタンのイベントリスナー
    refreshModelManagerBtn.addEventListener('click', () => {
        refreshModelManager();
    });
    
    // 設定ボタンのイベントリスナー
    settingsBtn.addEventListener('click', () => {
        settingsContainer.style.display = 'flex';
    });
    
    // 設定を閉じるボタンのイベントリスナー
    closeSettingsBtn.addEventListener('click', () => {
        settingsContainer.style.display = 'none';
    });
    
    // 設定をリセットするボタンのイベントリスナー
    resetSettingsBtn.addEventListener('click', () => {
        modelParams = { ...defaultParams };
        updateSettingsUI();
    });
    
    // 設定を保存するボタンのイベントリスナー
    saveSettingsBtn.addEventListener('click', async () => {
        const success = await updateModelParams();
        if (success) {
            settingsContainer.style.display = 'none';
            
            // 設定が保存されたことを通知
            addMessageToUI('system', 'モデルパラメータが更新されました。');
        }
    });
    
    // スライダーの値が変更されたときのイベントリスナー
    temperatureSlider.addEventListener('input', () => {
        const value = parseFloat(temperatureSlider.value);
        temperatureValue.textContent = value;
        modelParams.temperature = value;
    });
    
    topPSlider.addEventListener('input', () => {
        const value = parseFloat(topPSlider.value);
        topPValue.textContent = value;
        modelParams.top_p = value;
    });
    
    topKSlider.addEventListener('input', () => {
        const value = parseInt(topKSlider.value);
        topKValue.textContent = value;
        modelParams.top_k = value;
    });
    
    contextLengthSlider.addEventListener('input', () => {
        const value = parseInt(contextLengthSlider.value);
        contextLengthValue.textContent = value;
        modelParams.context_length = value;
    });
    
    repeatPenaltySlider.addEventListener('input', () => {
        const value = parseFloat(repeatPenaltySlider.value);
        repeatPenaltyValue.textContent = value;
        modelParams.repeat_penalty = value;
    });
    
    // メッセージ送信イベントのリスナー
    chatForm.addEventListener('submit', (e) => {
        e.preventDefault();
        
        // 処理中の場合は送信しない
        if (isProcessing) return;
        
        // 入力されたメッセージを取得
        const message = messageInput.value.trim();
        
        if (!message) return;
        
        // メッセージをUIに追加
        addMessageToUI('user', message);
        
        // 処理中状態に設定
        isProcessing = true;
        updateConnectionStatus('thinking');
        sendButton.disabled = true;
        
        // サーバーにメッセージを送信
        socket.emit('send_message', { message });
        
        // 入力フィールドをクリア
        messageInput.value = '';
    });
    
    // サーバーからのチャンク受信イベントのリスナー
    let currentAssistantMessage = null;
    let currentMessageDiv = null;
    
    socket.on('receive_chunk', (data) => {
        const content = data.content;
        
        // 最初のチャンクの場合、新しいメッセージ要素を作成
        if (!currentAssistantMessage) {
            currentAssistantMessage = '';
            
            // メッセージ要素の作成
            currentMessageDiv = document.createElement('div');
            currentMessageDiv.classList.add('message');
            currentMessageDiv.classList.add('assistant-message');
            
            // 送信者名を設定
            currentMessageDiv.innerHTML = `
                <div class="message-sender">アシスタント</div>
                <div class="message-content"></div>
            `;
            
            // メッセージをチャット領域に追加
            chatMessages.appendChild(currentMessageDiv);
        }
        
        // メッセージにチャンクを追加
        currentAssistantMessage += content;
        
        // メッセージの内容を更新
        const messageContent = currentMessageDiv.querySelector('.message-content');
        messageContent.innerHTML = escapeHtml(currentAssistantMessage);
        
        // 最新のメッセージが見えるようにスクロール
        chatMessages.scrollTop = chatMessages.scrollHeight;
    });
    
    // サーバーからのメッセージ受信イベントのリスナー
    socket.on('receive_message', (data) => {
        // ストリーミングの場合は、最終的なメッセージを表示
        if (data.sender === 'assistant' && currentMessageDiv) {
            // 既存のメッセージ要素を削除
            currentMessageDiv = null;
            currentAssistantMessage = null;
        } else {
            // 通常のメッセージを表示
            addMessageToUI(data.sender, data.message);
        }
        
        // 処理完了状態に設定
        isProcessing = false;
        updateConnectionStatus('ready');
        sendButton.disabled = false;
        messageInput.focus();
    });
    
    // ステータス更新イベントのリスナー
    socket.on('status_update', (data) => {
        updateConnectionStatus(data.status, data.message);
    });
    
    // 接続イベントのリスナー
    socket.on('connect', () => {
        updateConnectionStatus('connected');
    });
    
    // 切断イベントのリスナー
    socket.on('disconnect', () => {
        updateConnectionStatus('disconnected');
    });
}

/**
 * UIにメッセージを追加する関数
 *
 * @param {string} sender - メッセージの送信者（'user'または'assistant'または'system'）
 * @param {string} message - メッセージの内容
 */
function addMessageToUI(sender, message) {
    // メッセージ要素の作成
    const div = document.createElement('div');
    div.classList.add('message');
    div.classList.add(`${sender}-message`);
    
    // 送信者名を設定
    let senderName = 'システム';
    if (sender === 'user') {
        senderName = 'あなた';
    } else if (sender === 'assistant') {
        senderName = 'アシスタント';
    }
    
    // メッセージの内容を設定
    div.innerHTML = `
        <div class="message-sender">${senderName}</div>
        <div class="message-content">${escapeHtml(message)}</div>
    `;
    
    // メッセージをチャット領域に追加
    chatMessages.appendChild(div);
    
    // 最新のメッセージが見えるようにスクロール
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

/**
 * HTMLエスケープを行う関数
 *
 * @param {string} unsafe - エスケープする文字列
 * @returns {string} エスケープされた文字列
 */
function escapeHtml(unsafe) {
    return unsafe
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
}

/**
 * 接続状態の表示を更新する関数
 *
 * @param {string} status - 状態（'connected', 'disconnected', 'thinking', 'ready', 'error'）
 * @param {string} message - 表示するメッセージ（省略可）
 */
function updateConnectionStatus(status, message) {
    // すべてのステータスクラスを削除
    statusDot.classList.remove('connected', 'disconnected', 'thinking', 'error', 'ready');
    
    // 状態に応じたクラスを追加
    statusDot.classList.add(status);
    
    // 状態に応じたメッセージを設定
    if (message) {
        statusText.textContent = message;
    } else {
        switch (status) {
            case 'connected':
                statusText.textContent = '接続済み';
                break;
            case 'disconnected':
                statusText.textContent = '接続が切断されました';
                break;
            case 'thinking':
                statusText.textContent = '考え中...';
                break;
            case 'ready':
                statusText.textContent = '準備完了';
                break;
            case 'error':
                statusText.textContent = 'エラーが発生しました';
                break;
            default:
                statusText.textContent = status;
        }
    }
}