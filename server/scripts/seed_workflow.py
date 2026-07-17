# ============================================================================
# 初始化工作流按钮种子数据
# 运行: .venv/Scripts/python -c "from scripts.seed_workflow import run; run()"
# ============================================================================

def run():
    from flask import Flask
    from config import Config
    from utils import init_db, db
    from models.workflow import WorkflowAction
    from utils.logger import get_logger

    logger = get_logger(__name__)

    app = Flask(__name__)
    app.config.from_object(Config)
    init_db(app)

    with app.app_context():
        if WorkflowAction.query.count() > 0:
            # 已存在则更新 URL 为内部链接
            actions = WorkflowAction.query.all()
            internal_route = '/workflow'
            url_map = {
                '请假申请': f'{internal_route}/1',
                '加班申请': f'{internal_route}/2',
                '报销审批': f'{internal_route}/3',
                '出差申请': f'{internal_route}/4',
                '入职办理': f'{internal_route}/5',
            }
            for act in actions:
                if act.name in url_map:
                    act.url = url_map[act.name]
            db.session.commit()
            logger.info(f"已更新 {len(actions)} 个工作流按钮的 URL 为内部页面")
            return

        actions = [
            WorkflowAction(
                name='请假申请', keywords='请假,年假,病假,事假,调休,休假',
                label='📋 发起请假申请', url='/workflow/1',
                description='在线提交请假申请', sort_order=1,
            ),
            WorkflowAction(
                name='加班申请', keywords='加班,加班费,加班申请',
                label='⏰ 申请加班', url='/workflow/2',
                description='在线提交加班申请', sort_order=2,
            ),
            WorkflowAction(
                name='报销审批', keywords='报销,费用报销,发票,财务报销',
                label='💰 发起报销', url='/workflow/3',
                description='在线提交费用报销', sort_order=3,
            ),
            WorkflowAction(
                name='出差申请', keywords='出差,差旅,出差申请,差旅费',
                label='✈️ 申请出差', url='/workflow/4',
                description='在线提交出差申请', sort_order=4,
            ),
            WorkflowAction(
                name='入职办理', keywords='入职,报到,新员工,入职流程',
                label='👋 新员工入职', url='/workflow/5',
                description='新员工入职流程指引', sort_order=5,
            ),
        ]

        for a in actions:
            db.session.add(a)
        db.session.commit()
        logger.info(f"已创建 {len(actions)} 个工作流按钮")


if __name__ == '__main__':
    run()
