<template>
  <view class="ledger-page">
    <view class="summary-card">
      <text class="summary-label">校园动物救助基金余额</text>
      <text class="summary-amount">￥{{ formatMoney(totalBalance) }}</text>
      <text class="summary-tip">公开展示最近账目和物资库存</text>
    </view>

    <view class="section">
      <view class="section-head">
        <text class="section-title">财务流水</text>
        <text class="section-meta">最近 {{ ledgerList.length }} 条</text>
      </view>

      <view v-if="ledgerList.length === 0" class="empty-state">
        <text>暂无账目记录</text>
      </view>
      <view
        v-for="record in ledgerList"
        :key="record.id"
        class="record-card"
        @click="previewInvoice(record.invoiceUrl)"
      >
        <view class="record-main">
          <text class="record-desc">{{ record.desc }}</text>
          <text class="record-date">{{ record.date }}</text>
        </view>
        <view class="record-side">
          <text :class="['record-amount', record.type === 'income' ? 'income' : 'expense']">
            {{ record.type === 'income' ? '+' : '-' }}￥{{ formatMoney(record.amount) }}
          </text>
          <text class="voucher-text">{{ record.invoiceUrl ? '查看凭证' : '无凭证' }}</text>
        </view>
      </view>
    </view>

    <view class="section">
      <view class="section-head">
        <text class="section-title">物资库存</text>
        <text class="section-meta">{{ inventoryList.length }} 项</text>
      </view>

      <view v-if="inventoryList.length === 0" class="empty-state">
        <text>暂无库存记录</text>
      </view>
      <view class="inventory-grid">
        <view
          v-for="item in inventoryList"
          :key="item.id"
          :class="['inventory-card', item.isAlert ? 'inventory-alert' : '']"
        >
          <view class="inventory-top">
            <text class="inventory-name">{{ item.name }}</text>
            <text v-if="item.isAlert" class="alert-tag">需补充</text>
          </view>
          <text class="inventory-count">{{ item.count }}</text>
        </view>
      </view>
    </view>
  </view>
</template>

<script setup>
import { ref } from 'vue';
import { onShow, onPullDownRefresh } from '@dcloudio/uni-app';
import { config } from '@/config.js';

const totalBalance = ref(0);
const ledgerList = ref([]);
const inventoryList = ref([]);

const formatMoney = (value) => {
  const numberValue = Number(value || 0);
  return numberValue.toFixed(2);
};

const formatAssetUrl = (url) => {
  if (!url) return '';
  if (url.startsWith('http')) return url;
  const publicUrl = url.replace('/api/uploads/', '/static/uploads/');
  const prefix = publicUrl.startsWith('/') ? '' : '/';
  return `${config.baseUrl}${prefix}${publicUrl}`;
};

const previewInvoice = (url) => {
  const imageUrl = formatAssetUrl(url);
  if (!imageUrl) {
    uni.showToast({ title: '这条记录暂无凭证', icon: 'none' });
    return;
  }
  uni.previewImage({
    urls: [imageUrl],
    current: imageUrl,
  });
};

const fetchLedgerOverview = () => {
  uni.request({
    url: `${config.baseUrl}/api/ledger/overview`,
    method: 'GET',
    success: (res) => {
      if (res.data?.status !== 'success') {
        uni.showToast({ title: '账本加载失败', icon: 'none' });
        return;
      }

      const data = res.data.data || {};
      totalBalance.value = data.total_balance || 0;
      ledgerList.value = data.recent_transactions || [];
      inventoryList.value = data.inventory || [];
    },
    fail: () => {
      uni.showToast({ title: '无法连接账本接口', icon: 'none' });
    },
    complete: () => {
      uni.stopPullDownRefresh();
    },
  });
};

onShow(fetchLedgerOverview);
onPullDownRefresh(fetchLedgerOverview);
</script>

<style scoped>
.ledger-page {
  min-height: 100vh;
  background: #f5f7fa;
  padding: 18px;
  box-sizing: border-box;
}

.summary-card {
  background: #ffffff;
  border-radius: 14px;
  padding: 22px 18px;
  box-shadow: 0 8px 24px rgba(45, 55, 72, 0.08);
  border-left: 5px solid #ff9f43;
  display: flex;
  flex-direction: column;
}

.summary-label {
  color: #666;
  font-size: 14px;
}

.summary-amount {
  margin-top: 8px;
  color: #222;
  font-size: 34px;
  font-weight: 700;
  line-height: 42px;
}

.summary-tip {
  margin-top: 8px;
  color: #999;
  font-size: 12px;
}

.section {
  margin-top: 18px;
}

.section-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 10px;
}

.section-title {
  color: #222;
  font-size: 18px;
  font-weight: 700;
}

.section-meta {
  color: #999;
  font-size: 12px;
}

.empty-state {
  background: #fff;
  border-radius: 12px;
  padding: 28px 0;
  text-align: center;
  color: #999;
  font-size: 14px;
}

.record-card {
  background: #fff;
  border-radius: 12px;
  padding: 14px;
  margin-bottom: 10px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.03);
}

.record-main {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
}

.record-desc {
  color: #333;
  font-size: 15px;
  font-weight: 600;
}

.record-date {
  margin-top: 6px;
  color: #999;
  font-size: 12px;
}

.record-side {
  margin-left: 10px;
  display: flex;
  flex-direction: column;
  align-items: flex-end;
}

.record-amount {
  font-size: 16px;
  font-weight: 700;
}

.income {
  color: #2fb344;
}

.expense {
  color: #e03131;
}

.voucher-text {
  margin-top: 6px;
  color: #4facfe;
  font-size: 12px;
}

.inventory-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 10px;
}

.inventory-card {
  background: #fff;
  border-radius: 12px;
  padding: 14px;
  border: 1px solid #edf0f5;
}

.inventory-alert {
  border-color: #ffccc7;
  background: #fff7f6;
}

.inventory-top {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 8px;
}

.inventory-name {
  color: #333;
  font-size: 14px;
  font-weight: 600;
}

.alert-tag {
  flex-shrink: 0;
  background: #ff4d4f;
  color: #fff;
  border-radius: 9px;
  padding: 2px 7px;
  font-size: 10px;
}

.inventory-count {
  display: block;
  margin-top: 12px;
  color: #4facfe;
  font-size: 20px;
  font-weight: 700;
}
</style>
