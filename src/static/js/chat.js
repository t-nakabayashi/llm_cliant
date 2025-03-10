/**
 * ollama簡易クライアントのフロントエンド機能を実装するJavaScriptファイル
 */

// Socket.IOの接続を確立
const socket = io();

// DOM要素の取得
const modelSelection = document.getElementById('model-selection');
const chatContainer = document.getElementById('chat-container');
const settingsContainer = document.getElementById('settings-container');
const modelManagerContainer = document.getElementById('model-manager-container');
const modelList = document.getElementById('model-list');
const modelRunningInfo = document.getElementById('model-running-info');
const modelStatus = document.getElementById('model-status');
const currentModelName = document.getElementById('current-model-name');
const changeModelBtn = document.getElementById('change-model-btn');
const backToChatBtn = document.getElementById('back-to-chat-btn');
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

// サイドバー要素
const chatSidebar = document.querySelector('.chat-sidebar');
const sidebarToggleBtn = document.getElementById('sidebar-toggle-btn');
const sidebarRunningModels = document.getElementById('sidebar-running-models');
const sidebarGpuInfo = document.getElementById('sidebar-gpu-info');

// 設定関連の要素
const temperatureSlider = document.getElementById('temperature');
const temperatureValue = document.getElementById('temperature-value');
const topPSlider = document.getElementById('top-p');
const topPValue = document.getElementById('top-p-value');
const topKSlider = document.getElementById('top-k');
const topKValue = document.getElementById('top-k-value');
const contextLengthSlider = document.getElementById('context-length');
const contextLengthValue = document.getElementById('context-length-value');
const vramUsageValue = document.getElementById('vram-usage-value');
const repeatPenaltySlider = document.getElementById('repeat-penalty');
const repeatPenaltyValue = document.getElementById('repeat-penalty-value');
const resetSettingsBtn = document.getElementById('reset-settings-btn');
const saveSettingsBtn = document.getElementById('save-settings-btn');

// アプリケーションの状態
let currentModel = null;
let currentModelSize = 0; // モデルサイズ（バイト単位）
let isProcessing = false;
let modelParams = {
    temperature: 0.7,
    top_p: 0.9,
    top_k: 40,
    context_length: 4096,
    repeat_penalty: 1.1
};

// サイドバー更新用のタイマーID
let sidebarUpdateTimerId = null;

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
    // モデル一覧を取得（バックグラウンドで）
    fetchModels();
    
    // モデルパラメータを取得
    fetchModelParams();
    
    // イベントリスナーの設定
    setupEventListeners();
    
    // 初期画面をチャット画面に設定
    modelSelection.style.display = 'none';
    chatContainer.style.display = 'flex';
    
    // 初期メッセージを表示
    chatMessages.innerHTML = `
        <div class="message system-message">
            <div class="message-content">
                こんにちは！「モデル変更」ボタンからモデルを選択してチャットを開始できます。
            </div>
        </div>
    `;
});

/**
 * モデル一覧を取得する関数
 */
async function fetchModels() {
    try {
        // モデル一覧と起動中のモデルを並行して取得
        const [modelsResponse, runningModelsResponse] = await Promise.all([
            fetch('/api/models'),
            fetch('/api/running_models')
        ]);
        
        const modelsData = await modelsResponse.json();
        const runningModelsData = await runningModelsResponse.json();
        
        // 起動中のモデルを表示
        displayRunningModelsInSelection(runningModelsData.models || []);
        
        // 利用可能なモデル一覧を表示
        if (modelsData.models && modelsData.models.length > 0) {
            displayModels(modelsData.models, runningModelsData.models || []);
            modelStatus.textContent = 'モデルを選択してください';
            
            // チャットが開始されている場合は「戻る」ボタンを表示
            if (currentModel) {
                backToChatBtn.style.display = 'inline-block';
            }
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
 * モデル選択画面に起動中のモデルを表示する関数
 *
 * @param {Array} models - 起動中のモデル情報の配列
 */
function displayRunningModelsInSelection(models) {
    if (!models || models.length === 0) {
        modelRunningInfo.style.display = 'none';
        return;
    }
    
    modelRunningInfo.style.display = 'block';
    modelRunningInfo.innerHTML = `
        <div class="model-running-info-title">起動中のモデル</div>
    `;
    
    models.forEach(model => {
        const modelItem = document.createElement('div');
        modelItem.classList.add('running-model-item');
        
        modelItem.innerHTML = `
            <div class="running-model-info">
                <div class="running-model-name">${model.model}</div>
                <div class="running-model-id">ID: ${model.id}</div>
            </div>
            <button class="kill-model-btn" data-id="${model.id}">終了</button>
        `;
        
        modelRunningInfo.appendChild(modelItem);
        
        // 終了ボタンのイベントリスナー
        const killBtn = modelItem.querySelector('.kill-model-btn');
        killBtn.addEventListener('click', () => killModel(model.id));
    });
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
        
        if (data.models && data.models.length > 0) {
            displayRunningModels(data.models);
            displaySidebarRunningModels(data.models);
            return true;
        } else {
            runningModels.innerHTML = `
                <div class="no-models-message">
                    <p>起動中のモデルがありません。</p>
                </div>
            `;
            sidebarRunningModels.innerHTML = `
                <div class="no-models-message">
                    <p>起動中のモデルがありません。</p>
                </div>
            `;
            return false;
        }
    } catch (error) {
        console.error('起動中のモデル一覧の取得に失敗しました:', error);
        runningModels.innerHTML = `
            <div class="model-error">
                <p>起動中のモデル一覧の取得に失敗しました。ollamaサーバーが起動しているか確認してください。</p>
                <button onclick="refreshModelManager()" class="model-select-btn">再試行</button>
            </div>
        `;
        sidebarRunningModels.innerHTML = `
            <div class="model-error">
                <p>起動中のモデル一覧の取得に失敗しました。</p>
            </div>
        `;
        return false;
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
            displaySidebarGpuInfo(data.gpus);
            return true;
        } else {
            gpuInfo.innerHTML = `
                <div class="no-gpu-message">
                    <p>GPU情報を取得できませんでした。GPUが搭載されていないか、ドライバが正しくインストールされていない可能性があります。</p>
                </div>
            `;
            sidebarGpuInfo.innerHTML = `
                <div class="no-gpu-message">
                    <p>GPU情報を取得できませんでした。</p>
                </div>
            `;
            return false;
        }
    } catch (error) {
        console.error('GPU情報の取得に失敗しました:', error);
        gpuInfo.innerHTML = `
            <div class="model-error">
                <p>GPU情報の取得に失敗しました。</p>
                <button onclick="refreshModelManager()" class="model-select-btn">再試行</button>
            </div>
        `;
        sidebarGpuInfo.innerHTML = `
            <div class="model-error">
                <p>GPU情報の取得に失敗しました。</p>
            </div>
        `;
        return false;
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
 * サイドバーの情報を更新する関数
 */
async function updateSidebarInfo() {
    try {
        // 起動中のモデルとGPU情報を取得
        const [modelsResult, gpuResult] = await Promise.all([
            fetchRunningModels(),
            fetchGpuInfo()
        ]);
        
        // どちらも失敗した場合は更新を停止
        if (!modelsResult && !gpuResult) {
            console.warn('サイドバー情報の更新に失敗しました。更新を停止します。');
            stopSidebarUpdates();
        }
    } catch (error) {
        console.error('サイドバー情報の更新に失敗しました:', error);
    }
}

/**
 * サイドバーの定期更新を開始する関数
 */
function startSidebarUpdates() {
    // 既存のタイマーがあれば停止
    if (sidebarUpdateTimerId) {
        clearInterval(sidebarUpdateTimerId);
    }
    
    // 初回更新
    updateSidebarInfo();
    
    // 1秒おきに更新
    sidebarUpdateTimerId = setInterval(updateSidebarInfo, 1000);
}

/**
 * サイドバーの定期更新を停止する関数
 */
function stopSidebarUpdates() {
    if (sidebarUpdateTimerId) {
        clearInterval(sidebarUpdateTimerId);
        sidebarUpdateTimerId = null;
    }
}

/**
 * モデル一覧を表示する関数
 *
 * @param {Array} models - モデル情報の配列
 * @param {Array} runningModels - 起動中のモデル情報の配列
 */
function displayModels(models, runningModels = []) {
    modelList.innerHTML = '';
    
    // 起動中のモデル名のセット
    const runningModelNames = new Set(runningModels.map(m => m.model));
    
    models.forEach(model => {
        const modelCard = document.createElement('div');
        modelCard.classList.add('model-card');
        
        // 現在選択中または起動中のモデルの場合はクラスを追加
        if (model.name === currentModel) {
            modelCard.classList.add('selected');
        }
        
        // 起動中のモデルかどうかを確認
        const isRunning = runningModelNames.has(model.name);
        
        // モデルサイズをフォーマット
        const sizeInGB = model.size ? (model.size / (1024 * 1024 * 1024)).toFixed(2) + ' GB' : '不明';
        
        modelCard.innerHTML = `
            <div class="model-info">
                <div class="model-name">${model.name} ${isRunning ? '<span class="running-badge">起動中</span>' : ''}</div>
                <div class="model-details">サイズ: ${sizeInGB}</div>
            </div>
            <button class="model-select-btn" data-model="${model.name}">${isRunning ? '使用' : '選択'}</button>
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
    if (!models || models.length === 0) {
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
 * サイドバーに起動中のモデル一覧を表示する関数
 *
 * @param {Array} models - 起動中のモデル情報の配列
 */
function displaySidebarRunningModels(models) {
    if (!models || models.length === 0) {
        sidebarRunningModels.innerHTML = `
            <div class="no-models-message">
                <p>起動中のモデルがありません。</p>
            </div>
        `;
        return;
    }
    
    sidebarRunningModels.innerHTML = '';
    
    models.forEach(model => {
        const modelCard = document.createElement('div');
        modelCard.classList.add('sidebar-running-model');
        
        modelCard.innerHTML = `
            <div class="sidebar-running-model-name">${model.model}</div>
            <div class="sidebar-running-model-id">ID: ${model.id}</div>
        `;
        
        sidebarRunningModels.appendChild(modelCard);
    });
}

/**
 * GPU情報を表示する関数
 *
 * @param {Array} gpus - GPU情報の配列
 */
function displayGpuInfo(gpus) {
    if (!gpus || gpus.length === 0) {
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
                <div class="gpu-progress" style="width: ${memPercent}%"></div>
            </div>
        `;
        
        gpuInfo.appendChild(gpuCard);
    });
}

/**
 * サイドバーにGPU情報を表示する関数
 *
 * @param {Array} gpus - GPU情報の配列
 */
function displaySidebarGpuInfo(gpus) {
    if (!gpus || gpus.length === 0) {
        sidebarGpuInfo.innerHTML = `
            <div class="no-gpu-message">
                <p>GPU情報を取得できませんでした。</p>
            </div>
        `;
        return;
    }
    
    sidebarGpuInfo.innerHTML = '';
    
    gpus.forEach(gpu => {
        const gpuCard = document.createElement('div');
        gpuCard.classList.add('sidebar-gpu');
        
        // メモリ使用量をフォーマット
        const memUsed = gpu.memory_used ? `${gpu.memory_used.toFixed(0)} MB` : '不明';
        const memTotal = gpu.memory_total ? `${gpu.memory_total.toFixed(0)} MB` : '不明';
        const memPercent = gpu.memory_used_percent ? gpu.memory_used_percent.toFixed(1) : 0;
        
        gpuCard.innerHTML = `
            <div class="sidebar-gpu-header">
                <div class="sidebar-gpu-name">${gpu.name}</div>
                <div class="sidebar-gpu-utilization">${gpu.utilization.toFixed(1)}%</div>
            </div>
            <div class="sidebar-gpu-memory">${memUsed} / ${memTotal} (${memPercent}%)</div>
            <div class="sidebar-gpu-progress-bar">
                <div class="sidebar-gpu-progress" style="width: ${memPercent}%"></div>
            </div>
        `;
        
        sidebarGpuInfo.appendChild(gpuCard);
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
            
            // モデル選択画面を閉じる
            modelSelection.style.display = 'none';
            
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
                
                // モデルサイズを保存（利用可能な場合）
                const models = await (await fetch('/api/models')).json();
                const selectedModel = models.models.find(m => m.name === modelName);
                if (selectedModel && selectedModel.size) {
                    currentModelSize = selectedModel.size;
                    // VRAM使用量の表示を更新
                    updateVramUsage(modelParams.context_length);
                }
            }
            
            // 接続状態を更新
            updateConnectionStatus('ready');
            
            // サイドバーの定期更新を開始
            startSidebarUpdates();
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
    
    // VRAM使用量を更新
    updateVramUsage(modelParams.context_length);
}

/**
 * VRAM使用量を計算して表示する関数
 *
 * @param {number} contextLength - コンテキスト長
 */
function updateVramUsage(contextLength) {
    if (!currentModelSize) {
        vramUsageValue.textContent = '不明（モデルを選択してください）';
        return;
    }
    
    // モデルサイズとコンテキスト長からVRAM使用量を推定
    // 簡易的な計算式: モデルサイズ + (コンテキスト長 * 推定トークンサイズ)
    // トークンあたり約12バイトと仮定
    const tokenSizeBytes = 12;
    const baseModelSizeGB = currentModelSize / (1024 * 1024 * 1024);
    const contextSizeGB = (contextLength * tokenSizeBytes) / (1024 * 1024 * 1024);
    
    // 合計VRAM使用量（オーバーヘッドを考慮して20%増し）
    const totalVramGB = (baseModelSizeGB + contextSizeGB) * 1.2;
    
    // 表示を更新
    vramUsageValue.textContent = `約 ${totalVramGB.toFixed(2)} GB`;
}

/**
 * イベントリスナーを設定する関数
 */
function setupEventListeners() {
    // モデル変更ボタンのイベントリスナー
    changeModelBtn.addEventListener('click', () => {
        modelSelection.style.display = 'flex';
        fetchModels();
    });
    
    // モデル選択画面を閉じるボタンのイベントリスナー
    const closeModelSelectionBtn = document.getElementById('close-model-selection-btn');
    closeModelSelectionBtn.addEventListener('click', () => {
        modelSelection.style.display = 'none';
    });
    
    // サイドバー折りたたみボタンのイベントリスナー
    sidebarToggleBtn.addEventListener('click', () => {
        chatSidebar.classList.toggle('collapsed');
        const toggleIcon = sidebarToggleBtn.querySelector('.toggle-icon');
        if (chatSidebar.classList.contains('collapsed')) {
            toggleIcon.textContent = '◀';
            toggleIcon.style.transform = 'rotate(0deg)';
        } else {
            toggleIcon.textContent = '▶';
            toggleIcon.style.transform = 'rotate(180deg)';
        }
    });
    
    // チャットに戻るボタンのイベントリスナー（不要になったため削除）
    // backToChatBtn.addEventListener('click', () => {
    //     if (currentModel) {
    //         modelSelection.style.display = 'none';
    //
    //         // サイドバーの定期更新を開始
    //         startSidebarUpdates();
    //     }
    // });
    
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
        
        // VRAM使用量を計算して表示
        updateVramUsage(value);
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
        const messageElement = addMessageToUI('user', message);
        
        // ユーザーのメッセージが画面の一番上に来るようにスクロール
        if (messageElement) {
            messageElement.scrollIntoView({ behavior: 'smooth', block: 'start' });
        }
        
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
            
            // 送信者名を設定（現在のモデル名を使用）
            currentMessageDiv.innerHTML = `
                <div class="message-sender">${currentModel || 'モデル'}</div>
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
        scrollToBottom();
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
        
        // サイドバーの定期更新を停止
        stopSidebarUpdates();
    });
    
    // ページを離れる前にサイドバーの定期更新を停止
    window.addEventListener('beforeunload', () => {
        stopSidebarUpdates();
    });
}

/**
 * UIにメッセージを追加する関数
 *
 * @param {string} sender - メッセージの送信者（'user'または'assistant'または'system'）
 * @param {string} message - メッセージの内容
 * @returns {HTMLElement} 追加されたメッセージ要素
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
        senderName = currentModel || 'モデル';
    }
    
    // メッセージの内容を設定
    div.innerHTML = `
        <div class="message-sender">${senderName}</div>
        <div class="message-content">${escapeHtml(message)}</div>
    `;
    
    // メッセージをチャット領域に追加
    chatMessages.appendChild(div);
    
    // 最新のメッセージが見えるようにスクロール
    scrollToBottom();
    
    // 追加したメッセージ要素を返す
    return div;
}

/**
 * チャットメッセージ領域を最下部にスクロールする関数
 */
function scrollToBottom() {
    // スムーズにスクロール
    chatMessages.scrollTo({
        top: chatMessages.scrollHeight,
        behavior: 'smooth'
    });
}

/**
 * HTMLエスケープを行い、改行とコードブロックを処理する関数
 *
 * @param {string} unsafe - エスケープする文字列
 * @returns {string} エスケープされた文字列
 */
function escapeHtml(unsafe) {
    if (!unsafe) return '';
    
    // HTMLエスケープ
    let escaped = unsafe
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
    
    // コードブロックを検出して処理
    escaped = processCodeBlocks(escaped);
    
    // 改行を<br>タグに変換（コードブロック内は除く）
    escaped = escaped.replace(/\n(?!<\/code>|<code>)/g, "<br>");
    
    return escaped;
}

/**
 * コードブロックを処理する関数
 *
 * @param {string} text - 処理するテキスト
 * @returns {string} コードブロックが処理されたテキスト
 */
function processCodeBlocks(text) {
    // コードブロックのパターン: ```言語名\nコード\n```
    const codeBlockRegex = /```(\w*)\n([\s\S]*?)\n```/g;
    
    return text.replace(codeBlockRegex, function(match, language, code) {
        // 言語名が指定されていない場合は「code」とする
        const langClass = language ? `language-${language}` : 'language-code';
        
        // コードブロックのHTMLを生成
        return `
            <div class="code-block">
                <div class="code-header">
                    <span class="code-language">${language || 'コード'}</span>
                    <button class="copy-code-btn" onclick="copyCode(this)">コピー</button>
                </div>
                <pre><code class="${langClass}">${code}</code></pre>
            </div>
        `;
    });
}

/**
 * コードをクリップボードにコピーする関数
 *
 * @param {HTMLElement} button - コピーボタン要素
 */
function copyCode(button) {
    const codeBlock = button.closest('.code-block');
    const codeElement = codeBlock.querySelector('code');
    const code = codeElement.textContent;
    
    // クリップボードにコピー
    navigator.clipboard.writeText(code).then(() => {
        // コピー成功時の表示
        const originalText = button.textContent;
        button.textContent = 'コピー完了!';
        button.classList.add('copied');
        
        // 2秒後に元のテキストに戻す
        setTimeout(() => {
            button.textContent = originalText;
            button.classList.remove('copied');
        }, 2000);
    }).catch(err => {
        console.error('コピーに失敗しました:', err);
        button.textContent = 'コピー失敗';
        
        // 2秒後に元のテキストに戻す
        setTimeout(() => {
            button.textContent = 'コピー';
        }, 2000);
    });
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