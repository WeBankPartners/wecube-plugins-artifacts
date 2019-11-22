package com.webank.plugins.artifacts.service;

import static org.apache.commons.lang3.StringUtils.trim;

import java.util.List;
import java.util.Optional;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import com.webank.plugins.artifacts.commons.WecubeCoreException;
import com.webank.plugins.artifacts.domain.plugin.PluginInstance;
import com.webank.plugins.artifacts.domain.plugin.PluginPackage;
import com.webank.plugins.artifacts.jpa.PluginInstanceRepository;
import com.webank.plugins.artifacts.jpa.PluginPackageRepository;

@Service
@Transactional
public class PluginInstanceService {

    @Autowired
    PluginInstanceRepository pluginInstanceRepository;
    @Autowired
    PluginPackageRepository pluginPackageRepository;
  

    public List<PluginInstance> getRunningPluginInstances(String pluginName) {
        Optional<PluginPackage> pkg = pluginPackageRepository.findLatestVersionByName(pluginName);
        if (!pkg.isPresent()) {
            throw new WecubeCoreException(String.format("Plugin pacakge [%s] not found.", pluginName));
        }

        List<PluginInstance> instances = pluginInstanceRepository
                .findByStatusAndPackageId(PluginInstance.STATUS_RUNNING, pkg.get().getId());
        if (instances == null || instances.size() == 0) {
            throw new WecubeCoreException(String.format("No instance for plugin [%s] is available.", pluginName));
        }
        return instances;
    }

    public String getInstanceAddress(PluginInstance instance) {
        return trim(instance.getHost()) + ":" + trim(instance.getPort().toString());
    }
}
