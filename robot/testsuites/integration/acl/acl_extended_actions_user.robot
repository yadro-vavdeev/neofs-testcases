*** Settings ***
Variables    ../../../variables/common.py
Library      Collections
Library      ../${RESOURCES}/neofs.py
Library      ../${RESOURCES}/payment_neogo.py

Resource     common_steps_acl_extended.robot
Resource     ../${RESOURCES}/payment_operations.robot
Resource     ../${RESOURCES}/setup_teardown.robot
Resource     ../../../variables/eacl_tables.robot

*** Test cases ***
Extended ACL Operations
    [Documentation]         Testcase to validate NeoFS operations with extended ACL.
    [Tags]                  ACL  eACL  NeoFS  NeoCLI
    [Timeout]               20 min

    [Setup]                 Setup

                            Generate Keys

                            Log    Check extended ACL with simple object
                            Generate files    ${SIMPLE_OBJ_SIZE}
                            Check eACL Deny and Allow All User

                            Log    Check extended ACL with complex object
                            Generate files    ${COMPLEX_OBJ_SIZE}
                            Check eACL Deny and Allow All User

    [Teardown]              Teardown    acl_extended_action_user


*** Keywords ***

Check eACL Deny and Allow All User
                            Check eACL Deny and Allow All    ${USER_KEY}    ${EACL_DENY_ALL_USER}    ${EACL_ALLOW_ALL_USER}
