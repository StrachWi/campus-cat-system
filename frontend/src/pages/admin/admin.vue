<template>
  <view class="admin-container">
    <view class="admin-header">
      <text class="title">教师/管理员控制台</text>
      <text class="subtitle">校园猫咪信息管控中心</text>
    </view>

    <view class="tabs-container">
      <view
        v-for="tab in tabs"
        :key="tab.key"
        :class="['tab-item', currentTab === tab.key ? 'active-tab' : '']"
        @click="currentTab = tab.key"
      >
        {{ tab.label }}
      </view>
    </view>

    <view v-if="!token" class="notice-card">
      <text>请先从“我的”页面进入管理员审核端并完成登录。</text>
    </view>

    <view v-else class="content">
      <view v-show="currentTab === 'pending'">
        <view v-if="pendingCats.length === 0" class="empty-state">
          <text>当前没有待审核的猫咪档案</text>
        </view>
        <view class="review-card" v-for="cat in pendingCats" :key="cat.id" @click="openDetailModal(cat)">
          <view class="cat-info-row">
            <image class="cat-avatar" :src="formatImageUrl(cat.avatar_url)" mode="aspectFill"></image>
            <view class="cat-details">
              <text class="cat-name">{{ cat.name || '未命名猫咪' }}</text>
              <text class="cat-desc">位置：{{ cat.location || '未填写' }}</text>
              <text class="cat-desc">描述：{{ cat.character_desc || '未填写' }}</text>
            </view>
          </view>
          <view class="action-row">
            <button class="btn reject-btn" @click.stop="handleReview(cat.id, 'reject')">打回删除</button>
            <button class="btn pass-btn" @click.stop="handleReview(cat.id, 'pass')">审核通过</button>
          </view>
        </view>
      </view>

      <!-- 喵圈：管理员查看猫咪列表并认领喂养时段 -->
      <view v-show="currentTab === 'miaoguan'">
        <view v-if="miaoguanCats.length === 0" class="empty-state">
          <text>暂无已发布猫咪</text>
        </view>
        <view class="review-card" v-for="cat in miaoguanCats" :key="cat.id">
          <view class="cat-info-row" @click="openDetailModal(cat)">
            <image class="cat-avatar" :src="formatImageUrl(cat.avatar_url)" mode="aspectFill"></image>
            <view class="cat-details">
              <text class="cat-name">{{ cat.name || '未命名猫咪' }}</text>
              <text class="cat-desc">位置：{{ cat.location || '未填写' }}</text>
              <text class="cat-desc">描述：{{ cat.character_desc || '未填写' }}</text>
            </view>
          </view>
          <view class="feed-progress-box">
            <text class="progress-title">今日喂养排班：</text>
            <view class="admin-feed-row">
              <view v-for="meal in ['morning','noon','evening']" :key="meal" :class="['admin-meal-block', getAdminMealClass(meal, cat)]">
                <text class="admin-meal-name">{{ mealNameMap2[meal] }}</text>
                <text class="admin-meal-status">{{ getAdminMealText(meal, cat) }}</text>
                <button v-if="!cat.feed_status[meal]" class="admin-claim-btn" @click.stop="adminClaimMeal(cat.id, meal)">认领</button>
                <button v-else-if="cat.feed_status[meal] === adminUserId" class="admin-cancel-btn" @click.stop="adminCancelMeal(cat.id, meal)">取消</button>
                <text v-else class="admin-meal-taken">已认领</text>
              </view>
            </view>
          </view>
        </view>
      </view>

      <view v-show="currentTab === 'published'">
        <view v-if="publishedCats.length === 0" class="empty-state">
          <text>暂无已发布猫咪</text>
        </view>
        <view class="review-card" v-for="cat in publishedCats" :key="cat.id" @click="openDetailModal(cat)">
          <view class="cat-info-row">
            <image class="cat-avatar" :src="formatImageUrl(cat.avatar_url)" mode="aspectFill"></image>
            <view class="cat-details">
              <text class="cat-name">{{ cat.name || '未命名猫咪' }}</text>
              <text class="cat-desc">位置：{{ cat.location || '未填写' }}</text>
              <text class="cat-desc">描述：{{ cat.character_desc || '未填写' }}</text>
            </view>
          </view>
          <view class="action-row">
            <button class="btn reject-btn" @click.stop="handleDelete(cat.id)">下架并删除</button>
            <button class="btn pass-btn" @click.stop="openEditModal(cat)">修改信息</button>
          </view>
        </view>
      </view>

      <view v-show="currentTab === 'goods'">
        <view class="summary-card">
          <view class="summary-head">
            <text class="section-title">物资库存</text>
            <button class="small-btn" @click="getLedgerInfo">刷新</button>
          </view>
          <view v-if="goodsList.length === 0" class="empty-state compact">
            <text>暂无物资记录</text>
          </view>
          <view v-for="goods in goodsList" :key="goods.id" class="inventory-row">
            <view>
              <text class="inventory-name">{{ goods.name }}</text>
              <text :class="['inventory-count', goods.isAlert ? 'danger-text' : '']">
                当前库存：{{ goods.count }}
              </text>
            </view>
            <button class="small-btn danger" @click="handleDel(goods)">移除</button>
          </view>
        </view>

        <view class="form-card">
          <text class="section-title">物资入库 / 出库</text>
          <view class="segmented">
            <button :class="['segment', goodsForm.operate === 1 ? 'selected' : '']" @click="goodsForm.operate = 1">入库</button>
            <button :class="['segment', goodsForm.operate === 2 ? 'selected' : '']" @click="goodsForm.operate = 2">出库</button>
          </view>
          <view class="field">
            <text class="field-label">物资名称</text>
            <input class="input" v-model="goodsForm.item" placeholder="例如：成猫猫粮" />
          </view>
          <view class="field-grid">
            <view class="field">
              <text class="field-label">数量</text>
              <input class="input" type="digit" v-model="goodsForm.num" placeholder="1" />
            </view>
            <view class="field">
              <text class="field-label">单位</text>
              <input class="input" v-model="goodsForm.unit" placeholder="kg / 袋 / 个" />
            </view>
          </view>
          <view class="field">
            <text class="field-label">备注</text>
            <input class="input" v-model="goodsForm.remark" placeholder="来源或领用去向" />
          </view>
          <button class="primary-button" @click="submitGoods">保存物资改动</button>
        </view>
      </view>

      <view v-show="currentTab === 'bank'">
        <view class="summary-card">
          <text class="balance-label">当前基金余额</text>
          <text class="balance-amount">￥{{ formatMoney(balance) }}</text>
        </view>

        <view class="form-card">
          <text class="section-title">新增账目</text>
          <view class="segmented">
            <button :class="['segment', bankForm.type === 'income' ? 'selected' : '']" @click="bankForm.type = 'income'">收入</button>
            <button :class="['segment', bankForm.type === 'expense' ? 'selected' : '']" @click="bankForm.type = 'expense'">支出</button>
          </view>
          <view class="field">
            <text class="field-label">金额</text>
            <input class="input" type="digit" v-model="bankForm.amount" placeholder="0.00" />
          </view>
          <view class="field">
            <text class="field-label">备注</text>
            <input class="input" v-model="bankForm.remark" placeholder="款项来源或用途" />
          </view>
          <view class="field">
            <text class="field-label">凭证照片</text>
            <view class="upload-box" @click="chooseImage">
              <image v-if="bankForm.imagePath" :src="bankForm.imagePath" mode="aspectFill" class="preview-img"></image>
              <text v-else class="upload-placeholder">点击上传凭证</text>
            </view>
          </view>
          <button class="primary-button" @click="submitBank">保存账目</button>
        </view>

        <view class="summary-card">
          <view class="summary-head">
            <text class="section-title">最近流水</text>
            <button class="small-btn" @click="getLedgerInfo">刷新</button>
          </view>
          <view v-if="bankList.length === 0" class="empty-state compact">
            <text>暂无账目记录</text>
          </view>
          <view v-for="bill in bankList" :key="bill.id" class="bill-row" @click="previewInvoice(bill.invoiceUrl)">
            <view class="bill-left">
              <text class="bill-desc">{{ bill.desc }}</text>
              <text class="bill-date">{{ bill.date }}</text>
            </view>
            <text :class="['bill-amount', bill.type === 'income' ? 'green' : 'red']">
              {{ bill.type === 'income' ? '+' : '-' }}￥{{ formatMoney(bill.amount) }}
            </text>
          </view>
        </view>
      </view>
    </view>

    <view class="modal-mask" v-if="showEditModal">
      <view class="edit-modal">
        <text class="modal-title">修改猫咪信息</text>
        <input class="input" v-model="editForm.name" placeholder="猫咪名字" />
        <input class="input" v-model="editForm.location" placeholder="常出没地点" />
        <input class="input" v-model="editForm.character_desc" placeholder="性格描述" />
        <view class="modal-footer">
          <button class="btn reject-btn" @click="showEditModal = false">取消</button>
          <button class="btn pass-btn" @click="submitEdit">保存</button>
        </view>
      </view>
    </view>

    <!-- 猫咪详情弹窗 -->
    <view class="modal-mask" v-if="showDetailModal" @click="showDetailModal = false">
      <view class="detail-modal" @click.stop>
        <image class="detail-avatar" :src="formatImageUrl(detailCat.avatar_url)" mode="aspectFill"></image>
        <text class="detail-title">{{ detailCat.name || '未命名猫咪' }}</text>

        <view class="detail-grid">
          <view class="detail-item">
            <text class="detail-label">毛色</text>
            <text class="detail-value">{{ detailCat.color || '未填写' }}</text>
          </view>
          <view class="detail-item">
            <text class="detail-label">性别</text>
            <text class="detail-value">{{ detailCat.gender || '未知' }}</text>
          </view>
          <view class="detail-item">
            <text class="detail-label">绝育状态</text>
            <text class="detail-value">{{ detailCat.is_neutered ? '已绝育' : '未绝育' }}</text>
          </view>
          <view class="detail-item">
            <text class="detail-label">审核状态</text>
            <text :class="['detail-value', detailCat.audit_status === 'published' ? 'green' : 'red']">
              {{ detailCat.audit_status === 'published' ? '已发布' : '待审核' }}
            </text>
          </view>
        </view>

        <view class="detail-field">
          <text class="detail-label">常驻地点</text>
          <text class="detail-value">{{ detailCat.location || '未填写' }}</text>
        </view>
        <view class="detail-field">
          <text class="detail-label">性格特征</text>
          <text class="detail-value">{{ detailCat.character_desc || '未填写' }}</text>
        </view>
        <view class="detail-field">
          <text class="detail-label">健康状况</text>
          <text class="detail-value">{{ detailCat.health_status || '未填写' }}</text>
        </view>
        <view class="detail-field">
          <text class="detail-label">提报人ID</text>
          <text class="detail-value">{{ detailCat.user_id || '未知' }}</text>
        </view>

        <view class="detail-feed">
          <text class="detail-label">🐱 喂养认领状态</text>
          <view class="feed-row">
            <text>早餐：{{ detailCat.feed_status?.morning || '无人认领' }}</text>
            <text>午餐：{{ detailCat.feed_status?.noon || '无人认领' }}</text>
            <text>晚餐：{{ detailCat.feed_status?.evening || '无人认领' }}</text>
          </view>
        </view>

        <button class="primary-button" @click="showDetailModal = false" style="margin-top:16px;">关闭</button>
      </view>
    </view>
  </view>
</template>

<script setup>
import { reactive, ref } from 'vue';
import { onShow } from '@dcloudio/uni-app';
import { config } from '@/config.js';

const tabs = [
  { key: 'pending', label: '待审核' },
  { key: 'miaoguan', label: '喵圈' },
  { key: 'published', label: '已发布' },
  { key: 'goods', label: '物资管理' },
  { key: 'bank', label: '账目管理' },
];

const currentTab = ref('pending');
const token = ref('');
const userId = ref('');
const pendingCats = ref([]);
const publishedCats = ref([]);
const goodsList = ref([]);
const bankList = ref([]);
const balance = ref('0.00');
const showEditModal = ref(false);
const editForm = ref({ id: '', name: '', location: '', character_desc: '' });
const showDetailModal = ref(false);
const detailCat = ref({});

// ---- 喵圈 ----
const miaoguanCats = ref([]);
const adminUserId = ref('');
const mealNameMap2 = { morning: '早餐', noon: '午餐', evening: '晚餐' };

const goodsForm = reactive({
  operate: 1,
  item: '',
  num: '',
  unit: '',
  remark: '',
});

const bankForm = reactive({
  type: 'expense',
  amount: '',
  remark: '',
  imagePath: '',
});

const request = (options) => new Promise((resolve, reject) => {
  uni.request({
    ...options,
    success: resolve,
    fail: reject,
  });
});

const authHeader = () => ({ 'X-Admin-Token': token.value });

const formatMoney = (value) => Number(value || 0).toFixed(2);

const formatAssetUrl = (url) => {
  if (!url) return '';
  if (url.startsWith('http')) return url;
  const publicUrl = url.replace('/api/uploads/', '/static/uploads/');
  const prefix = publicUrl.startsWith('/') ? '' : '/';
  return `${config.baseUrl}${prefix}${publicUrl}`;
};

const formatImageUrl = (url) => {
  return formatAssetUrl(url) || 'https://images.unsplash.com/photo-1514888286974-6c03e2ca1dba?w=200&h=200&fit=crop';
};

const showError = (message) => {
  uni.showToast({ title: message, icon: 'none' });
};

const fetchPendingCats = async () => {
  const res = await request({
    url: `${config.baseUrl}/api/admin/pending_cats`,
    method: 'GET',
    header: authHeader(),
  });
  if (res.data?.status === 'success') {
    pendingCats.value = res.data.data || [];
  } else {
    showError(res.data?.message || '待审核数据加载失败');
  }
};

const fetchPublishedCats = async () => {
  const res = await request({
    url: `${config.baseUrl}/api/cats`,
    method: 'GET',
    header: authHeader(),
  });
  if (res.data?.status === 'success') {
    publishedCats.value = res.data.data || [];
  } else {
    showError(res.data?.message || '已发布数据加载失败');
  }
};

const getLedgerInfo = async () => {
  const res = await request({
    url: `${config.baseUrl}/api/ledger/overview`,
    method: 'GET',
  });
  if (res.data?.status !== 'success') {
    showError(res.data?.message || '账本数据加载失败');
    return;
  }
  const data = res.data.data || {};
  balance.value = data.total_balance || '0.00';
  goodsList.value = data.inventory || [];
  bankList.value = data.recent_transactions || [];
};

const refreshAll = async () => {
  if (!token.value) return;
  try {
    await Promise.all([fetchPendingCats(), fetchPublishedCats(), getLedgerInfo()]);
  } catch (err) {
    console.error(err);
    showError('无法连接后端，请确认 Flask 已启动');
  }
};

const handleReview = async (id, action) => {
  const res = await request({
    url: `${config.baseUrl}/api/admin/review_cat`,
    method: 'POST',
    header: authHeader(),
    data: { cat_id: id, action },
  });
  if (res.data?.status === 'success') {
    uni.showToast({ title: '操作成功', icon: 'success' });
    await Promise.all([fetchPendingCats(), fetchPublishedCats()]);
  } else {
    showError(res.data?.message || '操作失败');
  }
};

const handleDelete = (id) => {
  uni.showModal({
    title: '确认删除',
    content: '确定要彻底删除这只猫咪档案吗？',
    success: async (modal) => {
      if (!modal.confirm) return;
      const res = await request({
        url: `${config.baseUrl}/api/admin/delete_cat`,
        method: 'POST',
        header: authHeader(),
        data: { cat_id: id },
      });
      if (res.data?.status === 'success') {
        uni.showToast({ title: '已删除', icon: 'success' });
        await fetchPublishedCats();
      } else {
        showError(res.data?.message || '删除失败');
      }
    },
  });
};

const openEditModal = (cat) => {
  editForm.value = {
    id: cat.id,
    name: cat.name || '',
    location: cat.location || '',
    character_desc: cat.character_desc || '',
  };
  showEditModal.value = true;
};

const openDetailModal = (cat) => {
  detailCat.value = cat;
  showDetailModal.value = true;
};

// ==================== 喵圈功能 ====================
const fetchMiaoguanCats = async () => {
  const res = await request({
    url: `${config.baseUrl}/api/cats`,
    method: 'GET',
  });
  if (res.data?.status === 'success') {
    miaoguanCats.value = res.data.data || [];
  }
};

const getAdminMealClass = (meal, cat) => {
  const claimer = cat.feed_status?.[meal];
  if (!claimer) return 'meal-open';
  if (claimer === adminUserId.value) return 'meal-admin-claimed';
  return 'meal-other';
};

const getAdminMealText = (meal, cat) => {
  const claimer = cat.feed_status?.[meal];
  if (!claimer) return '无人认领';
  if (claimer === adminUserId.value) return '我已认领';
  return claimer;
};

const adminClaimMeal = async (catId, meal) => {
  const res = await request({
    url: `${config.baseUrl}/api/cats/${catId}/feed`,
    method: 'POST',
    header: authHeader(),
    data: { meal, action: 'claim', user_id: adminUserId.value },
  });
  if (res.data?.status === 'success') {
    uni.showToast({ title: '认领成功', icon: 'success' });
    await fetchMiaoguanCats();
  } else {
    showError('认领失败');
  }
};

const adminCancelMeal = async (catId, meal) => {
  const res = await request({
    url: `${config.baseUrl}/api/cats/${catId}/feed`,
    method: 'POST',
    header: authHeader(),
    data: { meal, action: 'cancel', user_id: adminUserId.value },
  });
  if (res.data?.status === 'success') {
    uni.showToast({ title: '已取消', icon: 'success' });
    await fetchMiaoguanCats();
  } else {
    showError('取消失败');
  }
};

const submitEdit = async () => {
  const res = await request({
    url: `${config.baseUrl}/api/admin/update_cat`,
    method: 'POST',
    header: authHeader(),
    data: {
      cat_id: editForm.value.id,
      name: editForm.value.name,
      location: editForm.value.location,
      character_desc: editForm.value.character_desc,
    },
  });
  if (res.data?.status === 'success') {
    uni.showToast({ title: '信息已更新', icon: 'success' });
    showEditModal.value = false;
    await fetchPublishedCats();
  } else {
    showError(res.data?.message || '保存失败');
  }
};

const submitGoods = async () => {
  const amount = Number(goodsForm.num);
  if (!goodsForm.item.trim()) return showError('请填写物资名称');
  if (!amount || amount <= 0) return showError('请填写正确数量');

  const res = await request({
    url: `${config.baseUrl}/api/admin/ledger/inventory/adjust`,
    method: 'POST',
    header: authHeader(),
    data: {
      operate: goodsForm.operate,
      item: goodsForm.item.trim(),
      num: amount,
      unit: goodsForm.unit.trim(),
      remark: goodsForm.remark.trim(),
    },
  });

  if (res.data?.status === 'success') {
    uni.showToast({ title: '物资已更新', icon: 'success' });
    goodsForm.item = '';
    goodsForm.num = '';
    goodsForm.unit = '';
    goodsForm.remark = '';
    await getLedgerInfo();
  } else {
    showError(res.data?.message === 'insufficient stock' ? '库存不足，无法出库' : (res.data?.message || '物资更新失败'));
  }
};

const handleDel = (goods) => {
  uni.showModal({
    title: '确认移除',
    content: `确定要移除“${goods.name}”吗？`,
    success: async (modal) => {
      if (!modal.confirm) return;
      const res = await request({
        url: `${config.baseUrl}/api/ledger/inventory/${goods.id}`,
        method: 'DELETE',
        header: authHeader(),
      });
      if (res.data?.status === 'success') {
        uni.showToast({ title: '删除成功', icon: 'success' });
        await getLedgerInfo();
      } else {
        showError(res.data?.message || '删除失败');
      }
    },
  });
};

const chooseImage = () => {
  uni.chooseImage({
    count: 1,
    sizeType: ['compressed'],
    sourceType: ['album', 'camera'],
    success: (res) => {
      bankForm.imagePath = res.tempFilePaths[0];
    },
  });
};

const submitBank = () => {
  const amount = Number(bankForm.amount);
  if (!amount || amount <= 0) return showError('请填写正确金额');
  if (!bankForm.remark.trim()) return showError('请填写备注');
  if (!bankForm.imagePath) return showError('请上传凭证照片');

  uni.uploadFile({
    url: `${config.baseUrl}/api/admin/ledger/transactions`,
    header: authHeader(),
    filePath: bankForm.imagePath,
    name: 'image',
    formData: {
      user_id: userId.value,
      amount,
      type: bankForm.type,
      remark: bankForm.remark.trim(),
    },
    success: async (res) => {
      const data = JSON.parse(res.data || '{}');
      if (data.status === 'success') {
        uni.showToast({ title: '账目已保存', icon: 'success' });
        bankForm.amount = '';
        bankForm.remark = '';
        bankForm.imagePath = '';
        await getLedgerInfo();
      } else {
        showError(data.message || '账目保存失败');
      }
    },
    fail: (err) => {
      console.error(err);
      showError('凭证上传失败，请确认后端已启动');
    },
  });
};

const previewInvoice = (url) => {
  const imageUrl = formatAssetUrl(url);
  if (!imageUrl) return showError('这条记录暂无凭证');
  uni.previewImage({ urls: [imageUrl], current: imageUrl });
};

onShow(() => {
  token.value = uni.getStorageSync('admin_token');
  userId.value = uni.getStorageSync('real_user_id') || '';
  adminUserId.value = String(uni.getStorageSync('real_user_id') || 'admin');
  refreshAll();
  fetchMiaoguanCats();
});
</script>

<style scoped>
.admin-container {
  min-height: 100vh;
  background-color: #f5f7fa;
  padding-bottom: 28px;
}

.admin-header {
  background: linear-gradient(135deg, #1787e0, #18d2d2);
  padding: 44px 18px 18px;
}

.title {
  display: block;
  font-size: 22px;
  font-weight: 700;
  color: #fff;
  margin-bottom: 8px;
}

.subtitle {
  color: rgba(255, 255, 255, 0.86);
  font-size: 13px;
}

.tabs-container {
  display: grid;
  grid-template-columns: repeat(5, 1fr);
  background: #fff;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.04);
}

.tab-item {
  text-align: center;
  padding: 14px 2px;
  font-size: 14px;
  color: #666;
  font-weight: 700;
  position: relative;
}

.active-tab {
  color: #1787e0;
}

.active-tab::after {
  content: '';
  position: absolute;
  left: 25%;
  right: 25%;
  bottom: 0;
  height: 3px;
  background: #1787e0;
  border-radius: 3px;
}

.content {
  padding: 14px;
}

.notice-card,
.summary-card,
.form-card,
.review-card {
  background: #fff;
  border-radius: 12px;
  padding: 16px;
  margin: 14px;
  box-shadow: 0 3px 12px rgba(0, 0, 0, 0.04);
}

.content .summary-card,
.content .form-card,
.content .review-card {
  margin: 0 0 14px;
}

.empty-state {
  text-align: center;
  color: #999;
  font-size: 14px;
  padding: 42px 0;
}

.compact {
  padding: 22px 0;
}

.cat-info-row {
  display: flex;
}

.cat-avatar {
  width: 72px;
  height: 72px;
  border-radius: 10px;
  margin-right: 12px;
  background: #eee;
}

.cat-details {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.cat-name {
  font-size: 17px;
  color: #222;
  font-weight: 700;
}

.cat-desc {
  color: #666;
  font-size: 13px;
}

.action-row,
.modal-footer {
  display: flex;
  gap: 10px;
  margin-top: 14px;
}

.btn,
.small-btn,
.primary-button,
.segment {
  margin: 0;
  border-radius: 8px;
  font-size: 14px;
}

.btn {
  flex: 1;
  height: 36px;
  line-height: 36px;
}

.pass-btn,
.primary-button {
  color: #fff;
  background: #1787e0;
}

.reject-btn,
.danger {
  color: #fff;
  background: #e03131;
}

.small-btn {
  height: 30px;
  line-height: 30px;
  padding: 0 12px;
  color: #1787e0;
  background: #eef7ff;
}

.summary-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.section-title {
  display: block;
  color: #222;
  font-size: 17px;
  font-weight: 700;
  margin-bottom: 12px;
}

.inventory-row,
.bill-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 0;
  border-top: 1px solid #f1f3f5;
}

.inventory-name,
.bill-desc {
  display: block;
  color: #222;
  font-size: 15px;
  font-weight: 600;
}

.inventory-count,
.bill-date {
  display: block;
  margin-top: 5px;
  color: #777;
  font-size: 12px;
}

.danger-text,
.red {
  color: #e03131;
}

.green {
  color: #2fb344;
}

.bill-left {
  flex: 1;
  min-width: 0;
}

.bill-amount {
  margin-left: 10px;
  font-size: 15px;
  font-weight: 700;
}

.balance-label {
  color: #666;
  font-size: 13px;
}

.balance-amount {
  display: block;
  margin-top: 8px;
  color: #222;
  font-size: 32px;
  font-weight: 800;
}

.segmented {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 8px;
  margin-bottom: 14px;
}

.segment {
  height: 36px;
  line-height: 36px;
  background: #f1f3f5;
  color: #555;
}

.selected {
  background: #1787e0;
  color: #fff;
}

.field {
  margin-bottom: 12px;
}

.field-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 10px;
}

.field-label {
  display: block;
  color: #555;
  font-size: 13px;
  margin-bottom: 6px;
}

.input {
  box-sizing: border-box;
  width: 100%;
  height: 40px;
  background: #f5f7fa;
  border-radius: 8px;
  padding: 0 12px;
  font-size: 14px;
}

.primary-button {
  width: 100%;
  height: 42px;
  line-height: 42px;
  margin-top: 6px;
}

.upload-box {
  height: 130px;
  border: 1px dashed #b8c2cc;
  border-radius: 10px;
  background: #f8fafc;
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
}

.upload-placeholder {
  color: #777;
  font-size: 14px;
}

.preview-img {
  width: 100%;
  height: 100%;
}

.modal-mask {
  position: fixed;
  inset: 0;
  z-index: 999;
  background: rgba(0, 0, 0, 0.45);
  display: flex;
  align-items: center;
  justify-content: center;
}

.edit-modal {
  width: 82%;
  background: #fff;
  border-radius: 14px;
  padding: 18px;
}

.modal-title {
  display: block;
  text-align: center;
  font-size: 18px;
  font-weight: 700;
  margin-bottom: 16px;
}

/* ===== 猫咪详情弹窗 ===== */
.detail-modal {
  width: 88%;
  max-height: 85vh;
  background: #fff;
  border-radius: 14px;
  padding: 20px;
  overflow-y: auto;
}

.detail-avatar {
  width: 100%;
  height: 220px;
  border-radius: 12px;
  background: #eee;
  margin-bottom: 14px;
}

.detail-title {
  display: block;
  text-align: center;
  font-size: 22px;
  font-weight: 800;
  color: #222;
  margin-bottom: 16px;
}

.detail-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
  margin-bottom: 12px;
}

.detail-item {
  background: #f5f7fa;
  border-radius: 10px;
  padding: 12px;
}

.detail-field {
  background: #f5f7fa;
  border-radius: 10px;
  padding: 12px;
  margin-bottom: 10px;
}

.detail-label {
  display: block;
  font-size: 12px;
  color: #999;
  margin-bottom: 5px;
}

.detail-value {
  font-size: 15px;
  color: #333;
  font-weight: 600;
}

.detail-feed {
  background: #fff8e1;
  border-radius: 10px;
  padding: 12px;
  margin-top: 4px;
}

.feed-row {
  display: flex;
  flex-direction: column;
  gap: 6px;
  margin-top: 8px;
  font-size: 14px;
  color: #555;
}

.green { color: #2fb344; }
.red { color: #e03131; }

/* ===== 喵圈喂养排班 ===== */
.feed-progress-box {
  background: #fafafa;
  padding: 10px;
  border-radius: 8px;
  margin-top: 10px;
}
.progress-title {
  font-size: 12px;
  color: #666;
  margin-bottom: 8px;
  display: block;
}
.admin-feed-row {
  display: flex;
  gap: 6px;
}
.admin-meal-block {
  flex: 1;
  text-align: center;
  padding: 10px 4px;
  border-radius: 10px;
  font-size: 12px;
}
.meal-open { background: #eee; color: #666; }
.meal-admin-claimed { background: #e3f2fd; color: #1976d2; border: 2px solid #1976d2; }
.meal-other { background: #e8f5e9; color: #388e3c; }
.admin-meal-name { display: block; font-weight: 700; margin-bottom: 3px; }
.admin-meal-status { display: block; font-size: 11px; margin-bottom: 4px; }
.admin-claim-btn {
  margin: 0 auto;
  padding: 2px 10px;
  font-size: 11px;
  border-radius: 12px;
  background: #1976d2;
  color: #fff;
  height: 24px;
  line-height: 24px;
}
.admin-cancel-btn {
  margin: 0 auto;
  padding: 2px 10px;
  font-size: 11px;
  border-radius: 12px;
  background: #fff;
  color: #1976d2;
  border: 1px solid #1976d2;
  height: 24px;
  line-height: 24px;
}
.admin-meal-taken { font-size: 11px; color: #999; }
</style>
