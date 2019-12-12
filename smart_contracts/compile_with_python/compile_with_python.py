# First make sure you install helios_solc using the command pip install py-helios-solc

from helios_solc import install_solc, compile_files

# First install the solidity binary v100.5.12 and above is helios solc
install_solc('v100.5.12')

# Next, compile your file. We will compile the delegated token contract
solidity_file = '../solidity/delegated_token.sol'
contract_name = 'HeliosDelegatedToken'
compiled_sol = compile_files([solidity_file])

# get the contract interface. This contains the binary, the abi etc...
contract_interface = compiled_sol['{}:{}'.format(solidity_file, contract_name)]

print("The compiled bin:")
print(contract_interface['bin'])
print("The compiled abi:")
print(contract_interface['abi'])

