
def assert_block_eq(testcase, block1, block2):
    
    if block1 != block2:
        msg = '%s != %s\n# Block 1 #########%s\n# Block 2 #########%s' %(block1, block2, block1.codestring, block2.codestring)
        testcase.fail(msg)
