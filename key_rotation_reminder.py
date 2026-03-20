#!/usr/bin/env python3
"""
API密钥轮换提醒脚本
根据安全策略提醒轮换API密钥
"""

import json
import os
from datetime import datetime, timedelta
from pathlib import Path

# 密钥轮换策略（天）
ROTATION_POLICY = {
    'high_risk': 90,      # 高风险：90天
    'medium_risk': 180,   # 中风险：180天
    'low_risk': 180,      # 低风险：180天
}

# 服务商风险等级
SERVICE_RISK_LEVELS = {
    'DeepSeek': 'high_risk',
    'SiliconFlow': 'high_risk',
    'Metaso': 'medium_risk',
    'IEEE_Xplore': 'medium_risk',
    'CORE_API': 'low_risk',
    'OpenAI': 'high_risk',
    'Semantic_Scholar': 'low_risk',
}

class KeyRotationManager:
    def __init__(self, data_file='.key_rotation.json'):
        self.data_file = data_file
        self.keys_data = self.load_data()

    def load_data(self):
        """加载密钥轮换数据"""
        if Path(self.data_file).exists():
            try:
                with open(self.data_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                return {}
        return {}

    def save_data(self):
        """保存密钥轮换数据"""
        try:
            with open(self.data_file, 'w', encoding='utf-8') as f:
                json.dump(self.keys_data, f, indent=2, ensure_ascii=False)
            return True
        except IOError:
            return False

    def register_key(self, service, key_id, rotation_days=None):
        """注册新密钥"""
        if service not in self.keys_data:
            self.keys_data[service] = []

        # 获取风险等级
        risk_level = SERVICE_RISK_LEVELS.get(service, 'medium_risk')
        rotation_days = rotation_days or ROTATION_POLICY[risk_level]

        key_info = {
            'id': key_id,
            'created_at': datetime.now().isoformat(),
            'rotation_days': rotation_days,
            'risk_level': risk_level,
            'last_checked': datetime.now().isoformat(),
            'rotated': False
        }

        self.keys_data[service].append(key_info)
        self.save_data()
        return key_info

    def check_rotation_needed(self, service=None):
        """检查是否需要轮换密钥"""
        today = datetime.now()
        results = []

        services_to_check = [service] if service else self.keys_data.keys()

        for svc in services_to_check:
            if svc not in self.keys_data:
                continue

            for key_info in self.keys_data[svc]:
                created_at = datetime.fromisoformat(key_info['created_at'])
                rotation_days = key_info['rotation_days']
                due_date = created_at + timedelta(days=rotation_days)

                days_until_due = (due_date - today).days
                is_overdue = days_until_due < 0

                result = {
                    'service': svc,
                    'key_id': key_info['id'][:10] + '...' if len(key_info['id']) > 13 else key_info['id'],
                    'created_at': key_info['created_at'][:10],
                    'due_date': due_date.isoformat()[:10],
                    'days_until_due': days_until_due,
                    'is_overdue': is_overdue,
                    'risk_level': key_info['risk_level'],
                    'status': 'OVERDUE' if is_overdue else 'DUE_SOON' if days_until_due <= 7 else 'OK'
                }
                results.append(result)

        return results

    def mark_as_rotated(self, service, key_id):
        """标记密钥已轮换"""
        if service in self.keys_data:
            for key_info in self.keys_data[service]:
                if key_info['id'] == key_id:
                    key_info['rotated'] = True
                    key_info['rotated_at'] = datetime.now().isoformat()
                    self.save_data()
                    return True
        return False

    def generate_report(self):
        """生成轮换报告"""
        checks = self.check_rotation_needed()

        if not checks:
            return "No keys registered for rotation tracking."

        # 按状态分组
        overdue = [c for c in checks if c['status'] == 'OVERDUE']
        due_soon = [c for c in checks if c['status'] == 'DUE_SOON']
        ok = [c for c in checks if c['status'] == 'OK']

        report_lines = ["API Key Rotation Status Report"]
        report_lines.append("=" * 60)

        if overdue:
            report_lines.append("\n🔴 OVERDUE - Immediate Action Required:")
            for item in overdue:
                report_lines.append(f"  • {item['service']}: Key {item['key_id']}")
                report_lines.append(f"    Created: {item['created_at']}, Due: {item['due_date']}")
                report_lines.append(f"    Overdue by {-item['days_until_due']} days")

        if due_soon:
            report_lines.append("\n🟡 DUE SOON - Plan Rotation:")
            for item in due_soon:
                report_lines.append(f"  • {item['service']}: Key {item['key_id']}")
                report_lines.append(f"    Created: {item['created_at']}, Due: {item['due_date']}")
                report_lines.append(f"    Due in {item['days_until_due']} days")

        if ok:
            report_lines.append("\n🟢 OK - No Action Needed:")
            for item in ok:
                report_lines.append(f"  • {item['service']}: Key {item['key_id']}")
                report_lines.append(f"    Created: {item['created_at']}, Due: {item['due_date']}")
                report_lines.append(f"    Due in {item['days_until_due']} days")

        report_lines.append("\n" + "=" * 60)
        report_lines.append(f"Total Keys: {len(checks)}")
        report_lines.append(f"Overdue: {len(overdue)}, Due Soon: {len(due_soon)}, OK: {len(ok)}")

        return "\n".join(report_lines)

def main():
    """主函数"""
    manager = KeyRotationManager()

    print("API Key Rotation Manager")
    print("=" * 50)

    # 检查当前状态
    report = manager.generate_report()
    print(report)

    # 提供操作选项
    print("\nAvailable actions:")
    print("1. Register new API key")
    print("2. Mark key as rotated")
    print("3. View detailed report")
    print("4. Exit")

    try:
        choice = input("\nSelect action (1-4): ").strip()

        if choice == '1':
            service = input("Service name (e.g., DeepSeek): ").strip()
            key_id = input("API Key ID (first few chars): ").strip()
            if service and key_id:
                manager.register_key(service, key_id)
                print(f"✓ Key for {service} registered successfully")
            else:
                print("✗ Service name and key ID are required")

        elif choice == '2':
            service = input("Service name: ").strip()
            key_id = input("API Key ID: ").strip()
            if service and key_id:
                if manager.mark_as_rotated(service, key_id):
                    print(f"✓ Key for {service} marked as rotated")
                else:
                    print(f"✗ Key not found for {service}")
            else:
                print("✗ Service name and key ID are required")

        elif choice == '3':
            checks = manager.check_rotation_needed()
            print("\nDetailed Status:")
            print("-" * 50)
            for check in checks:
                status_icon = '🔴' if check['status'] == 'OVERDUE' else '🟡' if check['status'] == 'DUE_SOON' else '🟢'
                print(f"{status_icon} {check['service']}: {check['status']}")
                print(f"  Key: {check['key_id']}")
                print(f"  Created: {check['created_at']}, Due: {check['due_date']}")
                print(f"  Days: {check['days_until_due']}, Risk: {check['risk_level']}")
                print()

    except KeyboardInterrupt:
        print("\n\nExiting...")

if __name__ == "__main__":
    main()