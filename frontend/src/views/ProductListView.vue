<template>
  <div class="product-list-container">
    <el-container>
      <el-header class="page-header">
        <div class="header-left">
          <h2>商品列表</h2>
        </div>
        <div class="header-right">
          <template v-if="isLoggedIn">
            <el-button @click="$router.push('/cart')">购物车</el-button>
            <el-button @click="$router.push('/orders')">我的订单</el-button>
            <el-button @click="$router.push('/addresses')">收货地址</el-button>
          </template>
          <template v-else>
            <el-button type="primary" @click="$router.push('/login')">登录</el-button>
            <el-button @click="$router.push('/register')">注册</el-button>
          </template>
        </div>
      </el-header>

      <el-main>
        <!-- Search Bar -->
        <div class="search-bar">
          <el-input
            v-model="keyword"
            placeholder="搜索商品名称（至少2个字符）"
            clearable
            class="search-input"
            @keyup.enter="handleSearch"
          >
            <template #prepend>
              <el-button icon="Search" @click="handleSearch" />
            </template>
          </el-input>
          <el-button v-if="keyword" class="reset-btn" @click="handleReset">
            重置
          </el-button>
        </div>

        <!-- Loading -->
        <div v-if="loading" class="loading-area">
          <el-skeleton :rows="3" animated />
        </div>

        <!-- Empty -->
        <el-empty v-else-if="products.length === 0" description="暂无商品" />

        <!-- Product Grid -->
        <div v-else class="product-grid">
          <el-card
            v-for="product in products"
            :key="product.id"
            class="product-card"
            shadow="hover"
            @click="goToDetail(product.id)"
          >
            <div class="product-image">
              <img
                v-if="product.imageUrl"
                :src="product.imageUrl"
                :alt="product.name"
              />
              <div v-else class="image-placeholder">
                <el-icon :size="48"><Picture /></el-icon>
              </div>
            </div>
            <div class="product-info">
              <h3 class="product-name">{{ product.name }}</h3>
              <div class="product-price">&yen;{{ product.price.toFixed(2) }}</div>
              <div class="product-footer">
                <el-tag
                  :type="product.stock > 0 ? 'success' : 'danger'"
                  size="small"
                >
                  {{ product.stock > 0 ? `库存: ${product.stock}` : '缺货' }}
                </el-tag>
                <el-button
                  type="primary"
                  size="small"
                  :disabled="product.stock <= 0"
                  @click.stop="handleAddToCart(product)"
                >
                  加入购物车
                </el-button>
              </div>
            </div>
          </el-card>
        </div>

        <!-- Pagination -->
        <div v-if="total > 0" class="pagination-area">
          <el-pagination
            v-model:current-page="page"
            v-model:page-size="size"
            :page-sizes="[12, 20, 40, 60]"
            :total="total"
            layout="total, sizes, prev, pager, next"
            @current-change="handlePageChange"
            @size-change="handleSizeChange"
          />
        </div>
      </el-main>
    </el-container>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import api from '../utils/api'
import { isLoggedIn } from '../utils/auth'

const router = useRouter()

const keyword = ref('')
const products = ref<any[]>([])
const loading = ref(false)
const page = ref(1)
const size = ref(20)
const total = ref(0)

async function fetchProducts() {
  loading.value = true
  try {
    let res
    if (keyword.value.trim().length >= 2) {
      res = await api.get('/products/search', {
        params: {
          keyword: keyword.value.trim(),
          page: page.value,
          size: size.value
        }
      })
    } else {
      res = await api.get('/products', {
        params: {
          page: page.value,
          size: size.value
        }
      })
    }
    const data = res.data.data
    products.value = data.records || []
    total.value = data.total || 0
  } catch {
    products.value = []
    total.value = 0
  } finally {
    loading.value = false
  }
}

function handleSearch() {
  if (keyword.value.trim() && keyword.value.trim().length < 2) {
    ElMessage.warning('搜索关键词至少2个字符')
    return
  }
  page.value = 1
  fetchProducts()
}

function handleReset() {
  keyword.value = ''
  page.value = 1
  fetchProducts()
}

function handlePageChange(val: number) {
  page.value = val
  fetchProducts()
}

function handleSizeChange(val: number) {
  size.value = val
  page.value = 1
  fetchProducts()
}

function goToDetail(id: number) {
  router.push(`/products/${id}`)
}

async function handleAddToCart(product: any) {
  if (!isLoggedIn()) {
    ElMessage.warning('请先登录')
    router.push('/login')
    return
  }
  try {
    await api.post('/cart/items', {
      productId: product.id,
      quantity: 1
    })
    ElMessage.success(`已将 "${product.name}" 加入购物车`)
  } catch {
    // Error handled by interceptor
  }
}

onMounted(() => {
  fetchProducts()
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

.header-left h2 {
  margin: 0;
  font-size: 20px;
}

.search-bar {
  display: flex;
  gap: 12px;
  margin-bottom: 24px;
  max-width: 500px;
}

.search-input {
  flex: 1;
}

.reset-btn {
  flex-shrink: 0;
}

.loading-area {
  padding: 40px 0;
}

.product-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(240px, 1fr));
  gap: 16px;
}

.product-card {
  cursor: pointer;
  transition: transform 0.2s;
}

.product-card:hover {
  transform: translateY(-2px);
}

.product-image {
  width: 100%;
  height: 200px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #f5f7fa;
  border-radius: 4px;
  overflow: hidden;
}

.product-image img {
  max-width: 100%;
  max-height: 100%;
  object-fit: cover;
}

.image-placeholder {
  color: #c0c4cc;
}

.product-info {
  padding-top: 12px;
}

.product-name {
  margin: 0 0 8px;
  font-size: 15px;
  color: #303133;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.product-price {
  font-size: 18px;
  font-weight: 600;
  color: #f56c6c;
  margin-bottom: 10px;
}

.product-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.pagination-area {
  display: flex;
  justify-content: center;
  margin-top: 24px;
}
</style>
