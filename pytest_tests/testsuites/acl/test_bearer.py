import allure
import pytest

from python_keywords.acl import (EACLAccess, EACLOperation, EACLRole, EACLRule, create_eacl, form_bearertoken_file,
                                 set_eacl, wait_for_cache_expired)
from python_keywords.container_access import (check_custom_access_to_container, check_full_access_to_container,
                                              check_no_access_to_container)


@pytest.mark.sanity
@pytest.mark.acl
@pytest.mark.acl_bearer
class TestACLBearer:
    @pytest.mark.parametrize('role', [EACLRole.USER, EACLRole.OTHERS])
    def test_bearer_token_operations(self, wallets, eacl_container_with_objects, role):
        allure.dynamic.title(f"Testcase to validate NeoFS operations with {role.value} BearerToken")
        cid, objects_oids, file_path = eacl_container_with_objects
        user_wallet = wallets.get_wallet()
        deny_wallet = wallets.get_wallet(role)

        with allure.step(f'Check {role.value} has full access to container without bearer token'):
            check_full_access_to_container(deny_wallet.wallet_path, cid, objects_oids.pop(), file_path,
                                           wallet_config=deny_wallet.config_path)

        with allure.step(f'Set deny all operations for {role.value} via eACL'):
            eacl = [EACLRule(access=EACLAccess.DENY, role=role, operation=op) for op in EACLOperation]
            eacl_file = create_eacl(cid, eacl)
            set_eacl(user_wallet.wallet_path, cid, eacl_file)
            wait_for_cache_expired()

        with allure.step(f'Create bearer token for {role.value} with all operations allowed'):
            bearer_token = form_bearertoken_file(user_wallet.wallet_path, cid, [
                EACLRule(operation=op, access=EACLAccess.ALLOW, role=role)
                for op in EACLOperation])

        with allure.step(f'Check {role.value} without token has no access to all operations with container'):
            check_no_access_to_container(
                deny_wallet.wallet_path, cid, objects_oids.pop(), file_path,
                wallet_config=deny_wallet.config_path)

        with allure.step(f'Check {role.value} with token has access to all operations with container'):
            check_full_access_to_container(deny_wallet.wallet_path, cid, objects_oids.pop(), file_path,
                                           bearer=bearer_token, wallet_config=deny_wallet.config_path)

        with allure.step(f'Set allow all operations for {role.value} via eACL'):
            eacl = [EACLRule(access=EACLAccess.ALLOW, role=role, operation=op) for op in EACLOperation]
            eacl_file = create_eacl(cid, eacl)
            set_eacl(user_wallet.wallet_path, cid, eacl_file)
            wait_for_cache_expired()

        with allure.step(f'Check {role.value} without token has access to all operations with container'):
            check_full_access_to_container(deny_wallet.wallet_path, cid, objects_oids.pop(), file_path,
                                           wallet_config=deny_wallet.config_path)

    @allure.title('BearerToken Operations for compound Operations')
    def test_bearer_token_compound_operations(self, wallets, eacl_container_with_objects):
        cid, objects_oids, file_path = eacl_container_with_objects
        user_wallet = wallets.get_wallet()
        other_wallet = wallets.get_wallet(role=EACLRole.OTHERS)

        # Operations that we will deny for each role via eACL
        deny_map = {
            EACLRole.USER: [EACLOperation.DELETE],
            EACLRole.OTHERS: [EACLOperation.GET, EACLOperation.PUT, EACLOperation.GET_RANGE]
        }

        # Operations that we will allow for each role with bearer token
        bearer_map = {
            EACLRole.USER: [EACLOperation.DELETE, EACLOperation.PUT, EACLOperation.GET_RANGE],
            EACLRole.OTHERS: [EACLOperation.GET, EACLOperation.GET_RANGE],
        }

        deny_map_with_bearer = {
            EACLRole.USER: [op for op in deny_map[EACLRole.USER] if op not in bearer_map[EACLRole.USER]],
            EACLRole.OTHERS: [op for op in deny_map[EACLRole.OTHERS] if op not in bearer_map[EACLRole.OTHERS]],
        }

        eacl_deny = []
        for role, operations in deny_map.items():
            eacl_deny += [EACLRule(access=EACLAccess.DENY, role=role, operation=op) for op in operations]
        set_eacl(user_wallet.wallet_path, cid, eacl_table_path=create_eacl(cid, eacl_deny))
        wait_for_cache_expired()

        with allure.step('Check rule consistency without bearer'):
            check_custom_access_to_container(user_wallet.wallet_path, cid, objects_oids.pop(), file_path,
                                             deny_operations=deny_map[EACLRole.USER],
                                             wallet_config=user_wallet.config_path)
            check_custom_access_to_container(other_wallet.wallet_path, cid, objects_oids.pop(), file_path,
                                             deny_operations=deny_map[EACLRole.OTHERS],
                                             wallet_config=other_wallet.config_path)

        with allure.step('Check rule consistency with bearer'):
            bearer_token_user = form_bearertoken_file(user_wallet.wallet_path, cid, [
                EACLRule(operation=op, access=EACLAccess.ALLOW, role=EACLRole.USER)
                for op in bearer_map[EACLRole.USER]])

            bearer_token_other = form_bearertoken_file(user_wallet.wallet_path, cid, [
                EACLRule(operation=op, access=EACLAccess.ALLOW, role=EACLRole.OTHERS)
                for op in bearer_map[EACLRole.OTHERS]])

            check_custom_access_to_container(user_wallet.wallet_path, cid, objects_oids.pop(), file_path,
                                             deny_operations=deny_map_with_bearer[EACLRole.USER],
                                             bearer=bearer_token_user,
                                             wallet_config=user_wallet.config_path)
            check_custom_access_to_container(other_wallet.wallet_path, cid, objects_oids.pop(), file_path,
                                             deny_operations=deny_map_with_bearer[EACLRole.OTHERS],
                                             bearer=bearer_token_other,
                                             wallet_config=other_wallet.config_path)