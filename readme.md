# Proxmox Ubuntu VM Template Role

The role to set up the Ubuntu template on Proxmox VM.  It uses HashiCorp's packer for building the template.

The builder uses aut-generated username and password for Packer's operation. 
The username and password are stored in the tmp/packer* on the Ansible Machine. 
After the template is built, you must configure the CloudInit through the proxmox in order to get access to it.

Prior to build, it checks if vm with the same name or id already exists and skips build if it does. 
The build takes about 10 minutes. 

Basic usage: 
1. Create template
2. Clone it (using full clone and thin provision or ZFS pool with deduplication))
3. Configure CloudInit

Role mandatory variables:
    
    # The pool where template will be stored
    storage_pool:

    # The type of the storage pool (zfspool etc. refer to the Packer's documentation)
    storage_pool_type:

    # The network adapter where template will be connected to. 
    # It must have access to the proxmox host and internet during the build time.
    template_network_adapter: 
      model:
      bridge:
      vlan_tag: 

Role optional variables (and their defaults): 

    # The name of the template
    template_vm_name: "ubuntu-template"

    # The vmid of the template
    template_vm_id: "20000"
    
    # The iso file with the Ubuntu installation. 
    # It must be pre-loaded to the proxmox host 
    template_iso_file: "local:iso/ubuntu-22.04.1-live-server-amd64.iso"
 
Example usage: 

    hosts: pve
    roles:
      - role: proxmox-vm-ubuntu-template
        vars:
            storage_pool: "pool1"
            storage_pool_type: "zfspool"
            template_network_adapter:
              model: virtio
              bridge: vmbr1
              vlan_tag: '99'
