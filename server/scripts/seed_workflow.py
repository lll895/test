# ============================================================================
# 初始化工作流按钮种子数据
# 运行: .venv/Scripts/python -c "from scripts.seed_workflow import run; run()"
# ============================================================================

def run():
    from flask import Flask
    from config import Config
    from utils import init_db, db
    from models.workflow import WorkflowAction

    app = Flask(__name__)
    app.config.from_object(Config)
    init_db(app)

    with app.app_context():
        if WorkflowAction.query.count() > 0:
            print("[种子] 工作流按钮已存在，跳过")
            return

        actions = [
            WorkflowAction(
                name='请假申请', keywords='请假,年假,病假,事假,调休,休假',
                label='📋 发起请假申请', url='https://oa.company.com/leave',
                description='跳转 OA 系统发起请假审批', sort_order=1,
            ),
            WorkflowAction(
                name='加班申请', keywords='加班,加班费,加班申请',
                label='⏰ 申请加班', url='https://oa.company.com/overtime',
                description='跳转 OA 系统填写加班单', sort_order=2,
            ),
            WorkflowAction(
                name='报销审批', keywords='报销,费用报销,发票,财务报销',
                label='💰 发起报销', url='https://oa.company.com/reimbursement',
                description='跳转财务系统提交报销', sort_order=3,
            ),
            WorkflowAction(
                name='出差申请', keywords='出差,差旅,出差申请,差旅费',
                label='✈️ 申请出差', url='https://oa.company.com/travel',
                description='跳转 OA 系统填写出差申请', sort_order=4,
            ),
            WorkflowAction(
                name='入职办理', keywords='入职,报到,新员工,入职流程',
                label='👋 新员工入职', url='https://oa.company.com/onboarding',
                description='新员工入职流程指引', sort_order=5,
            ),
        ]

        for a in actions:
            db.session.add(a)
        db.session.commit()
        print(f"[种子] 已创建 {len(actions)} 个工作流按钮")


if __name__ == '__main__':
    run()
