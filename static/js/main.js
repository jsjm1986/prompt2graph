// API请求处理
const api = {
    async post(url, data) {
        try {
            const response = await axios.post(url, data);
            return response.data;
        } catch (error) {
            throw error.response ? error.response.data : error;
        }
    },

    async get(url) {
        try {
            const response = await axios.get(url);
            return response.data;
        } catch (error) {
            throw error.response ? error.response.data : error;
        }
    }
};

// 消息提示
const toast = {
    show(message, type = 'success') {
        Toastify({
            text: message,
            duration: 3000,
            gravity: "top",
            position: "right",
            backgroundColor: type === 'error' ? "#ff4444" : "#00C851",
        }).showToast();
    }
};

// 图谱操作
const graphOperations = {
    // 创建图谱
    async create(formData) {
        try {
            const result = await api.post('/graph/create', formData);
            toast.show('图谱创建成功');
            return result;
        } catch (error) {
            toast.show(error.message || '创建失败', 'error');
            throw error;
        }
    },

    // 更新图谱
    async update(graphId, formData) {
        try {
            const result = await api.post(`/graph/${graphId}/edit`, formData);
            toast.show('更新成功');
            return result;
        } catch (error) {
            toast.show(error.message || '更新失败', 'error');
            throw error;
        }
    },

    // 合并图谱
    async merge(sourceId, targetId) {
        try {
            const result = await api.post(`/graph/${sourceId}/merge`, {
                target_graph_id: targetId
            });
            toast.show('图谱合并成功');
            return result;
        } catch (error) {
            toast.show(error.message || '合并失败', 'error');
            throw error;
        }
    },

    // 导出图谱
    async export(graphId, format = 'json') {
        try {
            const result = await api.get(`/graph/${graphId}/export?format=${format}`);
            return result;
        } catch (error) {
            toast.show(error.message || '导出失败', 'error');
            throw error;
        }
    }
};

// 批量处理
const batchProcessing = {
    async process(files) {
        const formData = new FormData();
        files.forEach(file => {
            formData.append('files', file);
        });

        try {
            const result = await api.post('/graph/batch', formData);
            toast.show('批量处理完成');
            return result;
        } catch (error) {
            toast.show(error.message || '批量处理失败', 'error');
            throw error;
        }
    }
};

// 拖放上传
function initDragAndDrop(dropZone, onFilesDrop) {
    ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
        dropZone.addEventListener(eventName, preventDefaults, false);
    });

    function preventDefaults(e) {
        e.preventDefault();
        e.stopPropagation();
    }

    ['dragenter', 'dragover'].forEach(eventName => {
        dropZone.addEventListener(eventName, highlight, false);
    });

    ['dragleave', 'drop'].forEach(eventName => {
        dropZone.addEventListener(eventName, unhighlight, false);
    });

    function highlight(e) {
        dropZone.classList.add('highlight');
    }

    function unhighlight(e) {
        dropZone.classList.remove('highlight');
    }

    dropZone.addEventListener('drop', handleDrop, false);

    function handleDrop(e) {
        const dt = e.dataTransfer;
        const files = [...dt.files];
        onFilesDrop(files);
    }
}

// 初始化页面功能
document.addEventListener('DOMContentLoaded', () => {
    // 初始化文件上传区域
    const dropZone = document.querySelector('.upload-area');
    if (dropZone) {
        initDragAndDrop(dropZone, files => {
            batchProcessing.process(files);
        });
    }

    // 初始化导出按钮
    const exportButtons = document.querySelectorAll('.export-btn');
    exportButtons.forEach(btn => {
        btn.addEventListener('click', async (e) => {
            const graphId = e.target.dataset.graphId;
            const format = e.target.dataset.format;
            try {
                const data = await graphOperations.export(graphId, format);
                // 处理导出数据
                if (format === 'json') {
                    const blob = new Blob([JSON.stringify(data, null, 2)], {
                        type: 'application/json'
                    });
                    const url = URL.createObjectURL(blob);
                    const a = document.createElement('a');
                    a.href = url;
                    a.download = `graph_${graphId}.json`;
                    document.body.appendChild(a);
                    a.click();
                    document.body.removeChild(a);
                    URL.revokeObjectURL(url);
                }
            } catch (error) {
                console.error('Export failed:', error);
            }
        });
    });

    // 初始化合并按钮
    const mergeButtons = document.querySelectorAll('.merge-btn');
    mergeButtons.forEach(btn => {
        btn.addEventListener('click', async (e) => {
            const sourceId = e.target.dataset.sourceId;
            const targetId = document.querySelector('#mergeTarget').value;
            if (targetId) {
                try {
                    await graphOperations.merge(sourceId, targetId);
                } catch (error) {
                    console.error('Merge failed:', error);
                }
            }
        });
    });
});
