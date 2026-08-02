<template>
  <div class="product-detail-container">
    <el-container>
      <el-header class="page-header">
        <div class="header-left">
          <el-button text @click="$router.push('/products')">
            <el-icon><ArrowLeft /></el-icon>
            返回商品列表
          </el-button>
        </div>
        <div class="header-right">
          <template v-if="isLoggedIn">
            <el-button @click="$router.push('/cart')">购物车</el-button>
            <el-button @click="$router.push('/orders')">我的订单</el-button>
          </template>
          <template v-else>
            <el-button type="primary" @click="$router.push('/login')">登录</el-button>
          </template>
        </div>
      </el-header>

      <el-main>
        <!-- Loading -->
        <div v-if="loading" class="loading-area">
          <el-skeleton :rows="5" animated />
        </div>

        <!-- Not Found -->
        <el-empty v-else-if="!product" description="商品不存在" />

        <!-- Product Detail -->
        <el-card v-else class="detail-card">
          <div class="detail-layout">
            <!-- Product Image -->
            <div class="detail-image">
              <img
                v-if="product.imageUrl"
                :src="product.imageUrl"
                :alt="product.name"
              />
              <div v-else class="image-placeholder">
                <el-icon :size="80"><Picture /></el-icon>
                <p>暂无图片</p>
              </div>
            </div>

            <!-- Product Info -->
            <div class="detail-info">
              <h1 class="product-name">{{ product.name }}</h1>
              <div class="product-price">
                <span class="price-symbol">&yen;</span>
                <span class="price-value">{{ product.price.toFixed(2) }}</span>
              </div>
              <div class="product-stock">
                <span class="label">库存：</span>
                <el-tag
                  :type="product.stock > 0 ? 'success' : 'danger'"
                  size="large"
                >
                  {{ product.stock > 0 ? `有货 (${product.stock})` : '缺货' }}
                </el-tag>
              </div>
              <div class="product-description">
                <h3>商品描述</h3>
                <p>{{ product.description || '暂无描述' }}</p>
              </div>
              <div class="product-actions">
                <div class="quantity-row">
                  <span class="label">数量：</span>
                  <el-input-number
                    v-model="quantity"
                    :min="1"
                    :max="product.stock"
                    :disabled="product.stock <= 0"
                    size="large"
                  />
                </div>
                <div class="action-buttons">
                  <el-button
                    type="primary"
                    size="large"
                    :disabled="product.stock <= 0"
                    :loading="adding"
                    @click="handleAddToCart"
                  >
                    {{ product.stock <= 0 ? '已售罄' : '加入购物车' }}
                  </el-button>
                </div>
              </div>
            </div>
          </div>

          <!-- Product Images Gallery -->
          <div v-if="product.images && product.images.length > 0" class="gallery">
            <h3>商品图片</h3>
            <div class="gallery-grid">
              <div
                v-for="(img, index) in product.images"
                :key="index"
                class="gallery-item"
              >
                <img :src="img" :alt="`${product.name} - 图片${index + 1}`" />
              </div>
            </div>
          </div>
        </el-card>
      </el-main>
    </el-container>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import api from '../utils/api'
import { isLoggedIn } from '../utils/auth'

const route = useRoute()
const router = useRouter()
const product = ref<any>(null)
const loading = ref(false)
const adding = ref(false)
const quantity = ref(1)

async function fetchProduct() {
  const id = route.params.id
  loading.value = true
  try {
    const res = await api.get(`/products/${id}`)
    product.value = res.data.data
  } catch {
    product.value = null
  } finally {
    loading.value = false
  }
}

async function handleAddToCart() {
  if (!isLoggedIn()) {
    ElMessage.warning('请先登录')
    router.push('/login')
    return
  }
  if (!product.value || product.value.stock <= 0) return

  adding.value = true
  try {
    await api.post('/cart/items', {
      productId: product.value.id,
      quantity: quantity.value
    })
    ElMessage.success(`已将 ${quantity.value} 件 "${product.value.name}" 加入购物车`)
    quantity.value = 1
  } catch {
    // Error handled by interceptor
  } finally {
    adding.value = false
  }
}

onMounted(() => {
  fetchProduct()
})
</script>

<style scoped>
.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: #fff;
  padding: 0 24px;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.08);
  height: 60px;
}

.loading-area {
  padding: 40px 0;
}

.detail-card {
  max-width: 1000px;
  margin: 0 auto;
}

.detail-layout {
  display: flex;
  gap: 32px;
  flex-wrap: wrap;
}

.detail-image {
  width: 400px;
  height: 400px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #f5f7fa;
  border-radius: 8px;
  overflow: hidden;
  flex-shrink: 0;
}

.detail-image img {
  max-width: 100%;
  max-height: 100%;
  object-fit: cover;
}

.image-placeholder {
  text-align: center;
  color: #c0c4cc;
}

.detail-info {
  flex: 1;
  min-width: 300px;
}

.product-name {
  font-size: 24px;
  color: #303133;
  margin: 0 0 16px;
}

.product-price {
  margin-bottom: 16px;
}

.price-symbol {
  font-size: 18px;
  color: #f56c6c;
}

.price-value {
  font-size: 32px;
  font-weight: 700;
  color: #f56c6c;
}

.product-stock {
  margin-bottom: 16px;
  display: flex;
  align-items: center;
  gap: 8px;
}

.label {
  color: #606266;
  font-size: 14px;
}

.product-description {
  margin-bottom: 24px;
}

.product-description h3 {
  margin: 0 0 8px;
  font-size: 16px;
  color: #303133;
}

.product-description p {
  margin: 0;
  color: #606266;
  line-height: 1.6;
}

.product-actions {
  border-top: 1px solid #ebeef5;
  padding-top: 20px;
}

.quantity-row {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 16px;
}

.action-buttons {
  display: flex;
  gap: 12px;
}

.gallery {
  margin-top: 32px;
}

.gallery h3 {
  margin: 0 0 12px;
  font-size: 16px;
  color: #303133;
}

.gallery-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(150px, 1fr));
  gap: 12px;
}

.gallery-item {
  width: 100%;
  aspect-ratio: 1;
  border-radius: 4px;
  overflow: hidden;
  background: #f5f7fa;
}

.gallery-item img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}
</style>
