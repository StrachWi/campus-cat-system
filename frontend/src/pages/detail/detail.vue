<template>
  <view class="detail-container">
    <image class="cat-avatar" :src="formatImageUrl(catInfo?.avatar_url)" mode="aspectFill"></image>

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
          <view class="meal-info">
            <text class="meal-name">{{ mealNameMap[meal] }}</text>
            <text v-if="!catInfo.feed_status[meal]" class="meal-status status-pending">⌛ 待认领</text>
            <text v-else-if="catInfo.feed_status[meal] === myUserId" class="meal-status status-mine">✅ 我已认领</text>
            <text v-else class="meal-status status-others">🔒 已被其他爱心人士认领</text>
          </view>
          <button v-if="!catInfo.feed_status[meal]" class="action-btn claim-btn" @click="handleFeedAction(meal, 'claim')">认领</button>
          <button v-else-if="catInfo.feed_status[meal] === myUserId" class="action-btn cancel-btn" @click="handleFeedAction(meal, 'cancel')">取消</button>
          <button v-else class="action-btn disabled-btn" disabled>已被认领</button>
        </view>
      </view>
    </view>
	
	<view class="meal-plan">
		<view class="meal-item" v-for="feed in feedlist" :key = "feed">
			<text>{{feed.user}}在{{mealNameMap[trans(feed.time)]}}投喂了{{feed.type}}</text>
		</view>
	</view>
	
	<footer class="float-bottom-btn">
		<view class="myinfo">
		  <text v-if="!catInfo.feed_status[nowmeal]" class="meal-name1">还未有人来喂养</text>
		  <text v-else-if="catInfo.feed_status[nowmeal] === myUserId" class="meal-name1">我已经认领的</text>
		  <text v-else class="meal-name1">已有人要来喂养</text>
		</view>
		<button v-if="!catInfo.feed_status[nowmeal]" class="action-btn claim-btn" @click="handleFeedAction(nowmeal,'claim')">认领后可喂养</button>
		<button v-else-if="catInfo.feed_status[nowmeal] === myUserId" class="action-btn cancel-btn" @click="toggleDialog()">去喂养</button>
		<button v-else class="action-btn disabled-btn" disabled>暂时不能喂养</button>
	</footer>
  </view>
  
	<div v-if="isDialogVisible" class="dialog-wrapper">
      <div class="dialog">
        <h3>喂养提报</h3>
        <form @submit.prevent="handleSubmit()">
          <label>食物:</label>
		  <picker :value="foodtype" :range="foodlist" @change="onfoodch">
			  <view class="picktype"> {{ foodlist[foodtype] }} </view>
		  </picker>
		  <label>是否喂水:
		  <button type="button" :class=" ['check', checkbut ? 'ch-yes' : 'ch-no'] " @click="checkbut=!checkbut">是</button></label>
          <div class="actions">
            <button type="submit" @click="handleSubmit()">提交</button>
            <button type="button" @click="closeDialog()">取消</button>
          </div>
        </form>
      </div>
    </div>
  
</template>

<script setup>
import { ref ,reactive, computed} from 'vue';
import { onLoad, onShow } from '@dcloudio/uni-app';
import { config } from '@/config.js';

const catId = ref(null);
const catInfo = ref({});
const myUserId = ref(null);
const mealNameMap = { morning: '早餐', noon: '午餐', evening: '晚餐' };
const nowmeal = ref('morning')

const checkbut = ref(false);
const isDialogVisible = ref(false);
const food = ref('');
const water = ref('');
const foodtype = ref(0);
const foodlist = ref([ '猫粮', '猫条', '零食']);
const feedlist = ref([{user:'lihua',time:3,type:'猫条'}]);

const checkwater = ()=>{
	checkbut = !checkbut;
	if(checkbut) water.value='是';
	else water.value='否';
};
const toggleDialog = () => { isDialogVisible.value = true; };
const closeDialog = () => {
  isDialogVisible.value = false;
  // 重置表单数据
  food.value = '';
  water.value = '';
};

const trans = (meal) =>{
	if(meal.value === 1) return 'morning';
	else if(meal.value === 2) return 'noon';
	else return 'evening';
};

const trans2 = (ti) =>{
	if(ti.value ==='morning') return 1;
	else if(ti.value === 'noon') return 2;
	else return 3;
};

const handleSubmit = () => {
	uni.showModal({
		title:'上传猫咪喂养信息' , content:'确定要上传喂养记录吗？',
		success:(res)=>{
			if(res.confirm)
			  uni.request({
			  	url:`${config.baseUrl}/api/cats/feeding` , method:'POST',data:{user_id:myUserId , cat_id:catId, time:trans2(nowmeal) , food:food.value ,water:water.value},
				success: () => {
					uni.showToast({
						title:'formData'
					})
				}
			  });
		 }
	});
	fetchrecord();
  closeDialog();
};


const fed = computed(()=>{
	const temp = feedlist.value.filter(rec =>{
		return nowmeal.value===rec.time.value;
	});
});

const onfoodch =(e) =>{
	foodtype.value = e.detail.value;
	food.value = foodlist[foodtype.value];
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
});

onShow(() => {
  initUserId();
  if (catId.value) fetchCatDetail();
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
    url: `${config.baseUrl}/api/cats`, 
    method: 'GET',
    success: (res) => {
      if(res.data.status === 'success') {
        const allCats = res.data.data;
        const targetCat = allCats.find(c => c.id == catId.value);
        if (targetCat) {
          if (targetCat.avatar_url && !targetCat.avatar_url.startsWith('http')) {
            targetCat.avatar_url = config.baseUrl + targetCat.avatar_url;
          }
          catInfo.value = targetCat;
        }
      }
    }
  });
};

const fetchrecord=() =>{
	uni.request({
		url: `${config.baseUrl}/api/cats/feeding`,
		methon: 'GET',
		success:(res) =>{
			if(res.data.status == 'success') {
				feedlist.value = res.data.data;
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
.detail-container { min-height: 100vh; background-color: #f8f9fa; padding-bottom: 50px; }
.main-image { width: 100%; height: 260px; background-color: #eee; }
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

.action-btn { margin: 2px; font-size: 13px; border-radius: 20px; padding: 0 20px; height: 32px; line-height: 32px;}
.claim-btn { background-color: #ff8c00; color: #fff; }
.cancel-btn { background-color: #fff; color: #ff8c00; border: 1px solid #ff8c00; }
.disabled-btn { background-color: #f5f5f5; color: #ccc; }
.float-bottom-btn {position:fixed; width: 100% ;display: flex; justify-content: space-around;bottom: 0px; z-index: 99;background-color: #aaffff;padding: 2 2px;  }


.picktype{background-color: #aaffff; padding: 0 12px; border-radius: 8px; font-size: 14px; color: #333; width: 25%;margin: 5px;}
.input-box { background-color: #aaffff; font-size: 14px; color: #00ff00; padding: 8 8 px; border-style:inset; border-width:2px;}
.check {font-size: 12px; color: #000000; width: 20%;}
.ch-yes{ background-color: #ff5500;}
.ch-no{background-color: #eee;}
.dialog-wrapper {
  position: fixed; top: 0; left: 0; width: 100%; height: 100%;
  background-color: rgba(0, 0, 0, 0.5);
  display: flex; justify-content: center; align-items: center;
}
.dialog { background: #fff; padding: 20px; border-radius: 8px; min-width: 300px; }
.actions button { margin-right: 10px; margin-top: 10px; }
</style>
