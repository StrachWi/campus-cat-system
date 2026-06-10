<template>
  <view class="ledger-container">
    <view class="header">
      <text class="title">阳光账本</text>
    </view>

    <view class="section balance-section">
      <text class="balance-title">救助基金总余额</text>
      <view class="balance-amount">
        <text class="currency">¥</text>
        <text class="number">{{ totalBalance }}</text>
      </view>
    </view>

    <view class="section">
      <text class="section-title">📦 物资库存</text>
      <view class="grid-box">
        <view class="grid-item" v-for="(item, index) in inventoryList" :key="index" :class="{'alert-item': item.isAlert}">
          <text class="item-name">{{ item.name }}</text>
          <text class="item-count">剩余: {{ item.count }}</text>
          <text class="alert-tag" v-if="item.isAlert">急需捐赠</text>
        </view>
      </view>
    </view>

    <view class="section">
      <text class="section-title">💰 账目明细</text>
      <view class="bill-list">
        <view class="bill-item" v-for="(bill, index) in billList" :key="index" @click="previewInvoice(bill.invoiceUrl)">
          <view class="bill-left">
            <text class="bill-desc">{{ bill.desc }}</text>
            <text class="bill-date">{{ bill.date }}</text>
          </view>
          <view class="bill-right">
            <text class="bill-amount" :class="bill.type === 'income' ? 'green' : 'red'">
              {{ bill.type === 'income' ? '+' : '-' }} {{ bill.amount }}元
            </text>
            <text class="arrow-icon">></text>
          </view>
        </view>
      </view>
    </view>

  </view>
</template>

<script setup>
import { ref } from 'vue'

const totalBalance = ref('1,250.00')

const inventoryList = ref([
{ name: '幼猫猫粮', count: '5kg', isAlert: false },
  { name: '成猫猫粮', count: '0.5kg', isAlert: true },  // 告警：主粮不足
  { name: '驱虫药', count: '12支', isAlert: false },
  { name: '豆腐猫砂', count: '1袋', isAlert: true },   // 告警：高频消耗品快没了
  { name: '鸡肉主食罐', count: '35罐', isAlert: false },
  { name: '营养猫条', count: '120支', isAlert: false },
  { name: '诱捕笼', count: '2个', isAlert: false },      // 工具类展示
  { name: '外伤碘伏', count: '半瓶', isAlert: true }     // 告警：急救药品不足
])

const billList = ref([
  { 
    desc: '购买成猫猫粮', 
    date: '2023-10-25', 
    amount: 150, 
    type: 'expense',
    invoiceUrl: 'https://via.placeholder.com/600x800/ffdddd/ff4d4f.png?text=Invoice+Example' // 模拟网图
  },
  { 
    desc: '张同学爱心捐赠', 
    date: '2023-10-24', 
    amount: 50, 
    type: 'income',
    invoiceUrl: 'https://via.placeholder.com/600x800/ddffdd/52c41a.png?text=Donation+Record' // 模拟网图
  }
])

const previewInvoice = (url) => {
  if (!url) {
    uni.showToast({ title: '这条记录暂无凭证', icon: 'none' })
    return
  }
  
  uni.previewImage({
    urls: [url],     
    current: url     
  })
}
</script>

<style scoped>
.ledger-container { background-color: #f5f5f5; min-height: 100vh; padding: 20px; padding-bottom: 40px; }
.header { text-align: center; margin-bottom: 20px; }
.title { font-size: 24px; font-weight: bold; color: #333; }
.section { background: #fff; border-radius: 12px; padding: 18px; margin-bottom: 20px; box-shadow: 0 4px 12px rgba(0,0,0,0.03); }
.section-title { font-size: 17px; font-weight: bold; border-bottom: 1px solid #f0f0f0; padding-bottom: 12px; display: block; margin-bottom: 15px; color: #333;}

.balance-section { 
  text-align: center; 
  background: linear-gradient(135deg, #ff9a44 0%, #fc6076 100%); 
  color: white; 
  padding: 25px 15px; 
}
.balance-title { font-size: 14px; opacity: 0.9; margin-bottom: 8px; display: block; }
.balance-amount { display: flex; justify-content: center; align-items: baseline; }
.currency { font-size: 22px; margin-right: 4px; }
.number { font-size: 40px; font-weight: bold; font-family: 'Avenir', Helvetica, sans-serif;}

.grid-box { 
  display: grid; 
  grid-template-columns: repeat(2, 1fr); /* 强制分成均等的两列 */
  gap: 12px; 
}
.grid-item { 
  background: #f9f9f9; 
  padding: 16px 10px; 
  border-radius: 8px; 
  text-align: center; 
  display: flex; 
  flex-direction: column; 
  justify-content: center;
  align-items: center;
}
.item-name { font-weight: bold; margin-bottom: 6px; font-size: 15px; color: #333; }
.item-count { font-size: 13px; color: #666; }
.alert-item { background: #fff1f0; border: 1px solid #ff4d4f; }
.alert-tag { background: #ff4d4f; color: white; font-size: 11px; padding: 3px 8px; border-radius: 12px; margin-top: 8px; }

.bill-item { 
  display: flex; 
  justify-content: space-between; 
  align-items: center; 
  padding: 16px 0; 
  border-bottom: 1px dashed #eee; 
  transition: background-color 0.2s; 
}
.bill-item:active { background-color: #f9f9f9; } /* 增加点击下去时的微小变色反馈 */
.bill-item:last-child { border-bottom: none; padding-bottom: 0; }

.bill-left { display: flex; flex-direction: column; flex: 1; }
.bill-desc { font-size: 15px; color: #333; font-weight: 500;}
.bill-date { font-size: 12px; color: #999; margin-top: 6px; }

.bill-right { display: flex; align-items: center; }
.bill-amount { font-size: 16px; margin-right: 10px; font-family: 'Avenir', Helvetica, sans-serif;}
.green { color: #52c41a; font-weight: bold; }
.red { color: #ff4d4f; font-weight: bold; }
.arrow-icon { color: #ccc; font-size: 16px; font-family: monospace; }
</style>