<template>
  <view class="detail-container">
    <image class="main-image" :src="formatImageUrl(catInfo?.avatar_url)" mode="aspectFill"></image>

    <view class="info-section" v-if="catInfo.name">
      <view class="header-row">
        <text class="cat-name">{{ catInfo.name }}</text>
        <text class="gender-tag">{{ catInfo.gender === '公' ? '♂️' : '♀️' }}</text>
      </view>
      <view class="tag-row">
        <text class="tag">{{ catInfo.color }}</text>
        <text class="tag">{{ catInfo.is_neutered ? '已绝育' : '待绝育' }}</text>
        <text class="tag">健康：{{ catInfo.health_status }}</text>
      </view>
      
      <view class="desc-box">
        <text class="label">性格特征：</text>
        <text class="desc-content">{{ catInfo.character_desc || '暂无描述' }}</text>
      </view>
      
      <view class="location-box">
        <text class="label">常驻地点：</text>
        <text class="value">{{ catInfo.location }}</text>
      </view>
    </view>

    <view class="action-section" v-if="catInfo.feed_status">
      <view class="section-title">
        <text>🍱 今日喂养计划</text>
        <text class="tip">认领后请及时去投喂哦</text>
      </view>
      
      <view class="meal-plan">
        <view class="meal-item" v-for="meal in ['morning', 'noon', 'evening']" :key="meal">
          <view class="meal-info" >
            <text class="meal-name">{{ mealNameMap[meal] }}</text>
            <text v-if=" trans2(meal)<trans2(nowmeal)&&!catInfo.feed_status[meal]" class="meal-status status-timeout">！已超时</text>
			<text v-else-if="!catInfo.feed_status[meal]" class="meal-status status-pending">⌛ 待认领</text>
            <text v-else-if="catInfo.feed_status[meal] === myUserId" class="meal-status status-mine">✅ 我已认领</text>
            <text v-else class="meal-status status-others">🔒 已被其他爱心人士认领</text>
          </view>
		  <button v-if="trans2(meal)<trans2(nowmeal)&&!catInfo.feed_status[meal]" class="action-btn timeout-btn" disabled>已超时</button>
          <button v-else-if="!catInfo.feed_status[meal]" class="action-btn claim-btn" @click="handleFeedAction(meal, 'claim')">认领</button>
          <button v-else-if="catInfo.feed_status[meal] === myUserId" class="action-btn cancel-btn" @click="handleFeedAction(meal, 'cancel')">取消</button>
          <button v-else class="action-btn disabled-btn" disabled>已被认领</button>
        </view>
      </view>
    </view>
	
	<view class="meal-plan">
		<view class="feed-item" v-for="feed in feedlist" :key = "feed">
			<text class="feed-time">{{formdate(feed.created_at)}}:</text>
			<text class="feed-name"> {{feed.username}} </text> 
			<text class="feed-def"> 在 </text>
			<text class="feed-meal">{{mealNameMap[trans(feed.time)]}}</text>
			<text class="feed-def">  投喂了 </text>
			<text class="feed-food"> {{feed.food}}</text>
			<text v-if="feed.water==='是'">和水</text>
		</view>
	</view>
	
	<view class="float-bottom-btn">
		<text>当前:{{mealNameMap[nowmeal]}}</text>
		<view class="myinfo">
		  <text v-if="!catInfo.feed_status[nowmeal]" class="meal-name1">还未有人来喂养</text>
		  <text v-else-if="catInfo.feed_status[nowmeal] === myUserId" class="meal-name1">我已经认领的</text>
		  <text v-else class="meal-name1">已有人要来喂养</text>
		</view>
		<button v-if="!catInfo.feed_status[nowmeal]" class="action-btn claim-btn" @click="handleFeedAction(nowmeal,'claim')">认领后可喂养</button>
		<button v-else-if="catInfo.feed_status[nowmeal] === myUserId" class="action-btn cancel-btn" @click="toggleDialog()">去喂养</button>
		<button v-else class="action-btn disabled-btn" disabled>暂时不能喂养</button>
	</view>
  </view>
  
	<view v-if="isDialogVisible" class="dialog-wrapper">
      <view class="dialog">
        <text class="dialog-title">喂养提报</text>
        <view>
          <text class="form-label">食物:</text>
		  <input v-model="food" placeholder="输入食物或在下方选择" class="input-box" />
		  <picker :value="foodtype" :range="foodlist" @change="onfoodch">
			  <view class="picktype"> {{ foodlist[foodtype] }} </view>
		  </picker>
		  <view class="water-row">
        <text class="form-label">是否喂水:</text>
		    <button :class=" ['check', checkbut ? 'ch-yes' : 'ch-no'] " @click="checkbut=!checkbut">{{checkbut ? '是' : '否'}}</button>
      </view>
          <view class="actions">
            <button @click="handleSubmit()">提交</button>
            <button @click="closeDialog()">取消</button>
          </view>
        </view>
      </view>
    </view>
  
</template>

<script setup>
import { ref } from 'vue';
import { onLoad, onShow } from '@dcloudio/uni-app';
import { config } from '@/config.js';

const catId = ref(null);
const catInfo = ref({});
const myUserId = ref(null);
const mealNameMap = { morning: '早餐', noon: '午餐', evening: '晚餐' };
const nowmeal = ref('morning');


const checkbut = ref(false);
const isDialogVisible = ref(false);
const food = ref('');
const water = ref('');
const foodtype = ref(0);
const foodlist = ref([ '猫粮', '猫条', '零食']);
const feedlist = ref([{username:'lihua',time:3,food:'猫条'}]);

const toggleDialog = () => { isDialogVisible.value = true; };
const closeDialog = () => {
  isDialogVisible.value = false;
  food.value = '';
  water.value = '';
};

const trans = (meal) =>{
	if(meal === 1) return 'morning';
	else if(meal === 2) return 'noon';
	else return 'evening';
};

const trans2 = (ti) =>{
	if(ti ==='morning') return 1;
	else if(ti === 'noon') return 2;
	else return 3;
};

const formdate = (isoDate)=>{
	const date = new Date(isoDate);
	const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, '0'); // 月份从0开始，需加1并补零
    const day = String(date.getDate()).padStart(2, '0');
    const hours = String(date.getHours()).padStart(2, '0');
    const minutes = String(date.getMinutes()).padStart(2, '0');
    const seconds = String(date.getSeconds()).padStart(2, '0');
      
    return `${year}-${month}-${day}`;
};

const handleSubmit = () => {
	if(!food.value){
		uni.showToast({
			title:'食物不能为空',icon:'error'
		});
		return ;
	}
	if(checkbut.value){
		water.value = '是';
	}else {
		water.value = '否';
	}
	uni.showModal({
		title:'上传猫咪喂养信息' , content:'确定要上传喂养记录吗？',
		success:(res)=>{
			if(res.confirm)
			  uni.request({
			  	url:`${config.baseUrl}/api/cats/feeding` , method:'POST',data:{user_id:myUserId.value , cat_id:catId.value, time:trans2(nowmeal.value) , food:food.value,water:water.value},
				success: (res) => {
					if(res.data.status === 'success'){
						feedlist.value.push(res.data.data);
						feedlist.value.sort((b,a)=>new Date(a.created_at) - new Date(b.created_at));
						uni.showToast({
						title:'提交成功'
						})
					}
					else {uni.showToast({
						title:'网络错误，稍后重试'
					})}
				}
			  });
		 }
	});
  isDialogVisible.value=false;
};


const gettime = ()=>{
	const hour = new Date().getHours(); // 获取当前小时数 (0-23)
	  
	  if (hour >= 6 && hour < 11) {
	    return 'morning';
	  } else if (hour >= 11 && hour < 15) {
	    return 'noon'; 
	  } else {
	    return 'evening'; 
	  }
};

const onfoodch =(e) =>{
	foodtype.value = e.detail.value;
	food.value = foodlist.value[foodtype.value];
};

const initUserId = () => {
  let uid = uni.getStorageSync('real_user_id');
  if (uid) {
    myUserId.value = String(uid);
  } else {
    myUserId.value = null;
  }
};

onLoad((options) => {
  catId.value = options.id;
  fetchrecord();
});

onShow(() => {
  initUserId();
  if (catId.value) fetchCatDetail();
  nowmeal.value = gettime();
});

const formatImageUrl = (url) => {
  if (!url) {
    return 'https://images.unsplash.com/photo-1514888286974-6c03e2ca1dba?w=200&h=200&fit=crop';
  }
  
  let newUrl = url;
  
  if (newUrl.includes('192.168.43.202')) {
    newUrl = newUrl.replace(/http:\/\/192\.168\.43\.202:\d+/g, config.baseUrl);
  }
  
  if (newUrl.includes('/api/uploads/')) {
    newUrl = newUrl.replace('/api/uploads/', '/static/uploads/');
  }
  
  if (!newUrl.startsWith('http')) {
    const prefix = newUrl.startsWith('/') ? '' : '/';
    newUrl = config.baseUrl + prefix + newUrl;
  }
  
  return newUrl;
};

const fetchCatDetail = () => {
  uni.request({
    url: `${config.baseUrl}/api/cats/${catId.value}`,
    method: 'GET',
    success: (res) => {
      if(res.data.status === 'success') {
        catInfo.value = res.data.data;
      }
    }
  });
};

const fetchrecord=() =>{
	uni.request({
		url: `${config.baseUrl}/api/cats/${catId.value}/feeding`,
		method: 'GET',
		success:(res) =>{
			if(res.data.status == 'success') {
				feedlist.value = res.data.data;
				const now = new Date();
				const oneDaysAgo = new Date(now.getTime() - 24 * 60 * 60 * 1000);
				feedlist.value = feedlist.value.filter(item => new Date(item.created_at) >= oneDaysAgo);
			}
		}
	});
};

const handleFeedAction = (meal, action) => {
  if (!myUserId.value) {
    uni.navigateTo({ url: '/pages/login/login' });
    return;
  }

  const isClaim = action === 'claim';
  const actionText = isClaim ? '认领' : '取消认领';

  uni.showModal({
    title: '操作确认',
    content: `确定要${actionText} ${catInfo.value.name} 的${mealNameMap[meal]}吗？`,
    success: (res) => {
      if (res.confirm) {
        uni.request({
          url: `${config.baseUrl}/api/cats/${catId.value}/feed`,
          method: 'POST',
          data: { 
            meal: meal, 
            action: action,
            user_id: myUserId.value 
          },
          success: (res) => {
            if (res.data && res.data.status === 'success') {
              uni.showToast({ title: '操作成功', icon: 'success' });
              if (!catInfo.value.feed_status) catInfo.value.feed_status = {};
              catInfo.value.feed_status[meal] = res.data.new_claimer;
            } else {
              uni.showToast({ title: '服务器忙', icon: 'none' });
            }
          },
          fail: () => {
            uni.showToast({ title: '网络连接失败', icon: 'none' });
          }
        });
      }
    }
  });
};
</script>

<style scoped>
.detail-container { min-height: 100vh; background-color: #f8f9fa; padding-bottom: 82px; }
.main-image { width: 100%; height: 260px; background-color: #eee; display: block; }
.info-section { background-color: #fff; padding: 20px; border-radius: 0 0 24px 24px; margin-bottom: 12px; }
.header-row { display: flex; align-items: center; margin-bottom: 10px; }
.cat-name { font-size: 24px; font-weight: bold; color: #333; margin-right: 10px; }
.tag-row { display: flex; gap: 8px; margin-bottom: 15px; }
.tag { background-color: #f0f2f5; color: #666; padding: 4px 10px; border-radius: 6px; font-size: 12px; }

.desc-box { background: #fff9f0; padding: 12px; border-radius: 8px; margin-bottom: 12px; }
.label { color: #999; font-size: 14px; }
.desc-content { font-size: 14px; color: #ff8c00; font-style: italic; margin-left: 5px; }
.location-box { font-size: 14px; padding: 5px 0;}
.value { color: #333; font-weight: 500; margin-left: 5px;}

.action-section { background-color: #fff; padding: 20px; }
.section-title { display: flex; justify-content: space-between; align-items: baseline; margin-bottom: 20px; }
.section-title text:first-child { font-size: 18px; font-weight: bold; }
.tip { font-size: 11px; color: #ff8c00; }

.meal-plan { display: flex; flex-direction: column; gap: 15px; }
.meal-item { display: flex; justify-content: space-between; align-items: center; background-color: #fcfcfc; padding: 12px; border-radius: 12px; border: 1px solid #f5f5f5; }
.meal-name { font-size: 15px; font-weight: bold; display: block; margin: 4px; }
.meal-name1 { font-size: 22px;margin: 5px; }
.meal-status { font-size: 12px; }

.status-pending { color: #909399; }
.status-mine { color: #67c23a; font-weight: bold;}
.status-others { color: #999; }
.status-timeout{color: #ff0000;}

.action-btn { margin: 2px; font-size: 13px; border-radius: 20px; padding: 0 20px; height: 32px; line-height: 32px;}
.claim-btn { background-color: #ff8c00; color: #fff; }
.cancel-btn { background-color: #fff; color: #ff8c00; border: 1px solid #ff8c00; }
.disabled-btn { background-color: #f5f5f5; color: #ccc; }
.timeout-btn{background-color: #ff0000; color: #ff0000;}
.float-bottom-btn { position: fixed; left: 0; right: 0; bottom: 0; z-index: 99; display: flex; justify-content: space-around; align-items: center; background-color: #fff7e8; padding: 8px 10px; box-shadow: 0 -2px 10px rgba(0,0,0,0.06); box-sizing: border-box; }


.picktype{background-color: #ff5500; padding: 0 12px; border-radius: 8px; font-size: 14px; color: #333; width: 25%;margin: 5px;}
.input-box { background-color: #f5f7fa; font-size: 14px; color: #333; padding: 8px; border-style: inset; border-width: 2px; width: 90%; box-sizing: border-box; }
.check {font-size: 12px; color: #000000; width: 20%;}
.ch-yes{ background-color: #ff5500;}
.ch-no{background-color: #eee;}
.dialog-wrapper {
  position: fixed; top: 0; left: 0; width: 100%; height: 100%;
  background-color: rgba(0, 0, 0, 0.5);
  display: flex; justify-content: center; align-items: center;
}
.dialog { background: #fff; padding: 20px; border-radius: 8px; min-width: 300px; }
.dialog-title { display: block; font-size: 18px; font-weight: 700; margin-bottom: 12px; color: #333; }
.form-label { display: block; color: #555; font-size: 14px; margin: 8px 0 6px; }
.water-row { display: flex; align-items: center; gap: 10px; margin-top: 10px; }
.actions button { margin-right: 10px; margin-top: 10px; }

.feed-item{padding: 10px;display: flex; justify-content: space-between; align-items: center; background-color: #ffffff; padding: 12px; border-radius: 12px; border: 1px solid #f5f5f5;}
.feed-time{font-size: 13px;}
.feed-name{font-size: 15px; color: #005500;}
.feed-meal{font-size: 15px; color: #67c23a;}
.feed-food{font-size: 15px; color: #550000;}
.feed-def{font-size: 10px;}
</style>
