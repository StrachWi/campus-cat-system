<template>
  <view class="form-container">
    <view class="header-banner">
      <text class="title">📸 捕捉到一只小可爱？</text>
      <text class="subtitle">填写档案，让更多同学认识它，一起云养猫！</text>
    </view>

    <view class="form-card">
      <!-- 照片上传区 -->
      <view class="upload-section" @click="chooseImage">
        <image v-if="formData.tempImagePath" :src="formData.tempImagePath" mode="aspectFill" class="preview-img"></image>
        <view v-else class="upload-placeholder">
          <text class="plus-icon">+</text>
          <text>上传猫咪靓照</text>
        </view>
      </view>

      <!-- 信息填写区 -->
      <view class="input-group">
        <text class="label">给它起个暂定名 <text class="required">*</text></text>
        <input class="input-box" v-model="formData.name" placeholder="比如：三食堂小花" />
      </view>

      <view class="input-group row-group">
        <view class="half-width">
          <text class="label">毛色</text>
          <input class="input-box" v-model="formData.color" placeholder="如：三花 / 纯黑" />
        </view>
        <view class="half-width">
          <text class="label">目测性别</text>
          <picker @change="bindGenderChange" :value="genderIndex" :range="genderOptions">
            <view class="input-box picker-text">{{ genderOptions[genderIndex] }}</view>
          </picker>
        </view>
      </view>

      <view class="input-group">
        <text class="label">常驻地点 <text class="required">*</text></text>
        <input class="input-box" v-model="formData.location" placeholder="越详细越好，如：图书馆东侧草坪" />
      </view>

      <view class="input-group">
        <text class="label">性格特征 <text class="required">*</text></text>
        <input class="input-box" v-model="formData.character_desc" placeholder="比如：亲人随便撸 / 胆小怕生" />
      </view>

      <view class="input-group">
        <text class="label">健康观察 (选填)</text>
        <input class="input-box" v-model="formData.health_status" placeholder="如：看着挺健康 / 好像有眼疾" />
      </view>
    </view>

    <!-- 底部提交按钮 -->
    <view class="submit-area">
      <button class="submit-btn" @click="submitForm">提交档案</button>
      <text class="tips">提交后将进入审核，审核通过后即可在喵圈展示</text>
    </view>
  </view>
</template>

<script setup>
import { ref } from 'vue';

const genderOptions = ['未知', '公', '母'];
const genderIndex = ref(0);

const formData = ref({
  tempImagePath: '', // 存放选中的本地图片路径
  name: '',
  color: '',
  gender: '未知',
  location: '',
  character_desc: '',
  health_status: ''
});

// 选择性别
const bindGenderChange = (e) => {
  genderIndex.value = e.detail.value;
  formData.value.gender = genderOptions[genderIndex.value];
};

// 调起手机相册选图
const chooseImage = () => {
  uni.chooseImage({
    count: 1, // 只能选一张
    sizeType: ['compressed'],
    sourceType: ['album', 'camera'],
    success: (res) => {
      formData.value.tempImagePath = res.tempFilePaths[0];
    }
  });
};

// 提交表单逻辑
const submitForm = () => {
  // 1. 基础校验
  if (!formData.value.name || !formData.value.location || !formData.value.character_desc) {
    uni.showToast({ title: '带 * 号的为必填项哦', icon: 'none' });
    return;
  }
  if (!formData.value.tempImagePath) {
    uni.showToast({ title: '请至少上传一张照片', icon: 'none' });
    return;
  }

  uni.showLoading({ title: '提交中...' });

  // 2. 真实发送请求给 Python 后端
  uni.request({
    url: 'http://192.168.43.202:5000/api/cats', // 你的后端地址
    method: 'POST',
    data: {
      name: formData.value.name,
      color: formData.value.color,
      gender: formData.value.gender,
      location: formData.value.location,
      character_desc: formData.value.character_desc,
      health_status: formData.value.health_status
      // 注意：图片文件我们暂时没放在 data 里，后端会自动补齐占位图
    },
    success: (res) => {
      uni.hideLoading();
      if (res.data.status === 'success') {
        uni.showToast({ title: '提报成功，等待老师审核！', icon: 'success' });
        // 延迟 1.5 秒后自动退回首页
        setTimeout(() => { uni.navigateBack(); }, 1500);
      } else {
        uni.showToast({ title: '提交失败，请重试', icon: 'none' });
      }
    },
    fail: (err) => {
      uni.hideLoading();
      console.error(err);
      uni.showToast({ title: '网络开小差啦，连接不到服务器', icon: 'none' });
    }
  });
};
</script>

<style scoped>
.form-container { min-height: 100vh; background-color: #f8f9fa; padding-bottom: 40px; }
.header-banner { background-color: #fff3e0; padding: 30px 20px; border-radius: 0 0 20px 20px; }
.title { display: block; font-size: 20px; font-weight: bold; color: #ff8c00; margin-bottom: 8px; }
.subtitle { font-size: 13px; color: #d07b0e; }

.form-card { background: #fff; margin: -20px 15px 20px; border-radius: 16px; padding: 20px; box-shadow: 0 4px 12px rgba(0,0,0,0.05); position: relative; z-index: 10; }
.upload-section { display: flex; justify-content: center; margin-bottom: 25px; }
.upload-placeholder { width: 120px; height: 120px; background-color: #f5f5f5; border: 2px dashed #e0e0e0; border-radius: 12px; display: flex; flex-direction: column; justify-content: center; align-items: center; color: #999; font-size: 12px; }
.plus-icon { font-size: 32px; color: #ccc; margin-bottom: 4px; }
.preview-img { width: 120px; height: 120px; border-radius: 12px; }

.input-group { margin-bottom: 16px; }
.row-group { display: flex; gap: 15px; }
.half-width { flex: 1; }
.label { display: block; font-size: 13px; color: #666; margin-bottom: 8px; font-weight: 500; }
.required { color: #f56c6c; }
.input-box { background-color: #f9f9f9; height: 44px; padding: 0 12px; border-radius: 8px; font-size: 14px; color: #333; }
.picker-text { line-height: 44px; }

.submit-area { padding: 0 20px; margin-top: 30px; text-align: center; }
.submit-btn { background-color: #ff8c00; color: #fff; font-size: 16px; font-weight: bold; height: 48px; line-height: 48px; border-radius: 24px; margin-bottom: 12px; }
.tips { font-size: 11px; color: #999; }
</style>