# ============================================================================
# 企业知识库 RAG 问答系统 - 缓存预热脚本
# 功能：系统启动时预热常用缓存
# ============================================================================

def warm_cache():
    """
    预热缓存
    在应用启动后调用，提前加载常用的业务数据到缓存
    """
    from services.cache_service import cache_service

    if not cache_service.is_connected:
        print("[缓存预热] Redis 未连接，跳过预热")
        return

    print("[缓存预热] 开始预热关键数据...")

    try:
        # 预热文档分类
        from models.document import Category
        from utils import db
        categories = Category.query.order_by(Category.sort_order).all()
        if categories:
            cache_service.set_categories_cache([cat.to_dict() for cat in categories])
            print(f"[缓存预热] 分类数据已缓存 ({len(categories)} 条)")

        print("[缓存预热] 完成")

    except Exception as e:
        print(f"[缓存预热] 出错: {e}")
